import json
import uuid
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from hmac import new as hmac_new

from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from accounts.models import User
from audit.models import AuditLog
from audit.services import write_audit
from core.decorators import role_required

from .forms import FeeStructureForm
from .gateway import get_gateway
from .models import FeeStatement, FeeStructure, Payment
from .services import (
    CURRENT_TERM,
    NoActiveAllocation,
    NoFeeStructure,
    get_active_allocation,
    get_or_create_statement,
)


@role_required(User.Role.STUDENT)
def my_fees(request):
    allocation = get_active_allocation(request.user)
    fee_error = None
    if allocation is not None:
        try:
            get_or_create_statement(request.user, CURRENT_TERM)
        except NoFeeStructure:
            fee_error = "No fee structure is configured for your room type and current term."
        except NoActiveAllocation:
            allocation = None

    statements = FeeStatement.objects.filter(student=request.user)
    room_type = allocation.room.room_type if allocation is not None else None
    room_type_label = dict(FeeStructure.RoomType.choices).get(room_type, room_type)
    return render(
        request,
        "fees/my_fees.html",
        {
            "statements": statements,
            "room_type_label": room_type_label,
            "fee_error": fee_error,
            "has_allocation": allocation is not None,
        },
    )


@role_required(User.Role.STUDENT)
@require_POST
def pay(request, statement_id):
    with transaction.atomic():
        statement = get_object_or_404(
            FeeStatement.objects.select_for_update(),
            pk=statement_id,
            student=request.user,
        )
        amount = statement.balance
        if amount <= 0:
            messages.info(request, "There are no dues to pay for this term.")
            return redirect("fees:my_fees")

        payment = Payment.objects.create(
            statement=statement,
            amount=amount,
        )
        order_id, checkout_url = get_gateway().create_order(amount, payment.pk)
        if not isinstance(order_id, str) or not order_id or len(order_id) > 100:
            raise ValueError("Payment gateway returned an invalid order ID.")
        payment.gateway_order_id = order_id
        payment.save(update_fields=["gateway_order_id", "updated_at"])

    return redirect(checkout_url)


@role_required(User.Role.STUDENT)
@require_GET
def mock_checkout(request, payment_id):
    if settings.PAYMENT_GATEWAY.lower() != "mock":
        return HttpResponseNotFound()
    payment = get_object_or_404(
        Payment,
        pk=payment_id,
        statement__student=request.user,
        status=Payment.Status.PENDING,
    )
    if not payment.gateway_order_id:
        return HttpResponseNotFound()
    buttons = []
    for status, label in (
        (Payment.Status.SUCCESS, "Pay (test)"),
        (Payment.Status.FAILED, "Fail (test)"),
    ):
        payload = json.dumps(
            {
                "order_id": payment.gateway_order_id,
                "amount": str(payment.amount),
                "txn_id": f"mock_{uuid.uuid4().hex}",
                "status": status,
            },
            separators=(",", ":"),
        )
        signature = hmac_new(
            settings.PAYMENT_WEBHOOK_SECRET.encode(),
            payload.encode(),
            sha256,
        ).hexdigest()
        buttons.append(
            {"label": label, "payload": payload, "signature": signature}
        )
    return render(
        request,
        "fees/mock_checkout.html",
        {"buttons": buttons},
    )


@role_required(User.Role.STUDENT)
@require_GET
def razorpay_checkout(request, payment_id):
    if settings.PAYMENT_GATEWAY.lower() != "razorpay":
        return HttpResponseNotFound()
    payment = get_object_or_404(
        Payment,
        pk=payment_id,
        statement__student=request.user,
        status=Payment.Status.PENDING,
    )
    if not payment.gateway_order_id:
        return HttpResponseNotFound()
    return render(
        request,
        "fees/razorpay_checkout.html",
        {
            "payment": payment,
            "checkout_options": {
                "key": settings.RAZORPAY_KEY_ID,
                "amount": int(payment.amount * 100),
                "currency": "INR",
                "name": "Hostel Management System",
                "order_id": payment.gateway_order_id,
            },
        },
    )


def _webhook_details(data):
    if not isinstance(data, dict):
        raise ValueError("Payment payload must be an object.")
    event = data.get("event")
    payload = data.get("payload")
    payment_payload = payload.get("payment") if isinstance(payload, dict) else None
    entity = (
        payment_payload.get("entity")
        if isinstance(payment_payload, dict)
        else None
    )
    if entity:
        status = {
            "payment.captured": Payment.Status.SUCCESS,
            "order.paid": Payment.Status.SUCCESS,
            "payment.failed": Payment.Status.FAILED,
        }.get(event)
        if status is None:
            raise ValueError("Unsupported payment event.")
        return (
            entity.get("order_id"),
            Decimal(str(entity.get("amount"))) / 100,
            entity.get("id"),
            status,
        )
    return (
        data.get("order_id"),
        Decimal(str(data.get("amount"))),
        data.get("txn_id"),
        data.get("status"),
    )


@csrf_exempt
@require_POST
def webhook(request):
    gateway = get_gateway()
    if request.content_type == "application/json":
        body = request.body
        signature = request.headers.get("X-Razorpay-Signature", "")
    else:
        payload = request.POST.get("payload")
        body = payload.encode() if payload is not None else request.body
        signature = (
            request.POST.get("signature")
            or request.headers.get("X-Razorpay-Signature", "")
        )

    if not gateway.verify_signature(body, signature):
        with transaction.atomic():
            write_audit(
                request.user,
                "PAYMENT_WEBHOOK_REJECTED",
                outcome=AuditLog.Outcome.DENIED,
                details={"reason": "invalid_signature"},
            )
        return HttpResponseBadRequest("Invalid signature.")

    try:
        data = json.loads(body)
        order_id, amount, txn_id, status = _webhook_details(data)
        amount = Decimal(amount)
    except (json.JSONDecodeError, InvalidOperation, TypeError, ValueError):
        return HttpResponseBadRequest("Invalid payment payload.")

    if (
        not amount.is_finite()
        or amount < 0
        or status not in (Payment.Status.SUCCESS, Payment.Status.FAILED)
    ):
        return HttpResponseBadRequest("Invalid payment amount or status.")
    if not isinstance(order_id, str) or not order_id:
        return HttpResponseNotFound("Unknown payment order.")

    with transaction.atomic():
        try:
            payment = Payment.objects.select_for_update().get(
                gateway_order_id=order_id
            )
        except Payment.DoesNotExist:
            return HttpResponseNotFound("Unknown payment order.")

        if payment.status == Payment.Status.SUCCESS:
            return HttpResponse(status=200)

        if amount != payment.amount:
            write_audit(
                request.user,
                "PAYMENT_WEBHOOK_REJECTED",
                payment,
                outcome=AuditLog.Outcome.DENIED,
                details={"reason": "amount_mismatch"},
            )
            return HttpResponseBadRequest("Payment amount does not match.")

        statement = FeeStatement.objects.select_for_update().get(
            pk=payment.statement_id
        )
        payment.status = status
        payment.gateway_txn_id = txn_id or None
        payment.save(update_fields=["status", "gateway_txn_id", "updated_at"])

        if status == Payment.Status.SUCCESS:
            statement.amount_paid += payment.amount
            statement.save(update_fields=["amount_paid"])
            write_audit(
                request.user,
                "PAYMENT_SUCCEEDED",
                payment,
                details={"amount": str(payment.amount)},
            )
            transaction.on_commit(
                lambda: send_mail(
                    subject="Hostel fee payment confirmed",
                    message=(
                        f"Your payment of {payment.amount} for "
                        f"{statement.term} has been confirmed."
                    ),
                    from_email=None,
                    recipient_list=[statement.student.email],
                    fail_silently=False,
                )
            )
        else:
            write_audit(
                request.user,
                "PAYMENT_FAILED",
                payment,
                outcome=AuditLog.Outcome.FAILED,
                details={"amount": str(payment.amount)},
            )

    return HttpResponse(status=200)


@role_required(User.Role.ADMIN, User.Role.WARDEN)
def structure_list(request):
    structures = FeeStructure.objects.all()
    return render(
        request,
        "fees/structure_list.html",
        {"structures": structures},
    )


@role_required(User.Role.ADMIN, User.Role.WARDEN)
def structure_create(request):
    form = FeeStructureForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            structure = form.save()
            write_audit(request.user, "FEE_STRUCTURE_SAVED", structure)
        messages.success(request, "Fee structure created.")
        return redirect("fees:structure_list")
    return render(
        request,
        "fees/structure_form.html",
        {"form": form, "is_edit": False},
    )


@role_required(User.Role.ADMIN, User.Role.WARDEN)
def structure_edit(request, pk):
    structure = get_object_or_404(FeeStructure, pk=pk)
    form = FeeStructureForm(request.POST or None, instance=structure)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            structure = form.save()
            write_audit(request.user, "FEE_STRUCTURE_SAVED", structure)
        messages.success(request, "Fee structure updated.")
        return redirect("fees:structure_list")
    return render(
        request,
        "fees/structure_form.html",
        {"form": form, "is_edit": True, "structure": structure},
    )
