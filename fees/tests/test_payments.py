import hashlib
import hmac
import json
from datetime import date
from decimal import Decimal

import pytest
from django.conf import settings
from django.urls import reverse
from django.test import override_settings

from accounts.models import User
from audit.models import AuditLog
from fees.gateway import RazorpayGateway
from fees.models import FeeStatement, Payment


@pytest.fixture
def student(db):
    return User.objects.create_user(
        "payment_student",
        email="payment-student@pes.edu",
        password="test-password-123",
        role=User.Role.STUDENT,
    )


@pytest.fixture
def statement(student):
    return FeeStatement.objects.create(
        student=student,
        term="2026-ODD",
        amount_due=Decimal("25000.00"),
        amount_paid=Decimal("5000.00"),
        due_date=date(2026, 8, 1),
    )


@pytest.fixture
def payment(statement):
    return Payment.objects.create(
        statement=statement,
        amount=Decimal("20000.00"),
        gateway_order_id="mock_test_order",
    )


def post_webhook(client, payment, *, status="SUCCESS", amount="20000.00", signature=None):
    payload = json.dumps(
        {
            "order_id": payment.gateway_order_id,
            "amount": amount,
            "txn_id": "mock_test_transaction",
            "status": status,
        },
        separators=(",", ":"),
    )
    signature = signature or hmac.new(
        settings.PAYMENT_WEBHOOK_SECRET.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()
    return client.post(
        reverse("fees:webhook"),
        data=payload,
        content_type="application/json",
        HTTP_X_RAZORPAY_SIGNATURE=signature,
    )


def test_successful_webhook_updates_payment_and_statement(client, payment, statement):
    response = post_webhook(client, payment, status=Payment.Status.SUCCESS)

    assert response.status_code == 200
    payment.refresh_from_db()
    statement.refresh_from_db()
    assert payment.status == Payment.Status.SUCCESS
    assert payment.gateway_txn_id == "mock_test_transaction"
    assert statement.amount_paid == Decimal("25000.00")
    assert AuditLog.objects.filter(action="PAYMENT_SUCCEEDED").count() == 1


def test_webhook_rejects_bad_signature_and_audits_denial(client, payment):
    response = post_webhook(client, payment, signature="invalid")

    assert response.status_code == 400
    payment.refresh_from_db()
    assert payment.status == Payment.Status.PENDING
    assert AuditLog.objects.filter(
        action="PAYMENT_WEBHOOK_REJECTED",
        outcome=AuditLog.Outcome.DENIED,
    ).exists()


def test_replayed_success_webhook_credits_only_once(client, payment, statement):
    first_response = post_webhook(client, payment)
    second_response = post_webhook(client, payment)

    assert first_response.status_code == second_response.status_code == 200
    statement.refresh_from_db()
    assert statement.amount_paid == Decimal("25000.00")
    assert AuditLog.objects.filter(action="PAYMENT_SUCCEEDED").count() == 1


def test_webhook_rejects_amount_mismatch(client, payment, statement):
    response = post_webhook(client, payment, amount="19999.99")

    assert response.status_code == 400
    payment.refresh_from_db()
    statement.refresh_from_db()
    assert payment.status == Payment.Status.PENDING
    assert statement.amount_paid == Decimal("5000.00")


def test_failed_webhook_does_not_change_statement_balance(client, payment, statement):
    response = post_webhook(client, payment, status=Payment.Status.FAILED)

    assert response.status_code == 200
    payment.refresh_from_db()
    statement.refresh_from_db()
    assert payment.status == Payment.Status.FAILED
    assert statement.amount_paid == Decimal("5000.00")


def test_pay_now_creates_pending_payment_and_redirects_to_checkout(
    client, student, statement
):
    client.force_login(student)

    response = client.post(reverse("fees:pay", args=[statement.pk]))

    payment = Payment.objects.get(statement=statement)
    assert response.status_code == 302
    assert response["Location"] == reverse(
        "fees:mock_checkout",
        args=[payment.pk],
    )
    assert payment.status == Payment.Status.PENDING
    assert payment.amount == Decimal("20000.00")


def test_pay_now_reports_zero_balance(client, student, statement):
    statement.amount_paid = statement.amount_due
    statement.save(update_fields=["amount_paid"])
    client.force_login(student)

    response = client.post(reverse("fees:pay", args=[statement.pk]), follow=True)

    assert response.status_code == 200
    assert b"There are no dues to pay for this term." in response.content
    assert not Payment.objects.exists()


def test_mock_checkout_offers_signed_test_outcomes(client, student, payment):
    client.force_login(student)

    response = client.get(
        reverse("fees:mock_checkout", args=[payment.pk])
    )

    assert response.status_code == 200
    assert b"Pay (test)" in response.content
    assert b"Fail (test)" in response.content


def test_student_fee_page_offers_pay_now(client, student, statement):
    client.force_login(student)

    response = client.get(reverse("fees:my_fees"))

    assert response.status_code == 200
    assert b"Pay now" in response.content


@override_settings(PAYMENT_GATEWAY="razorpay")
def test_razorpay_signature_verification_does_not_require_sdk():
    body = b'{"event":"payment.captured"}'
    signature = hmac.new(
        settings.PAYMENT_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    assert RazorpayGateway().verify_signature(body, signature)


def test_payment_has_no_card_data_fields():
    field_names = {field.name.casefold() for field in Payment._meta.get_fields()}

    assert not any(
        "card" in name or "cvv" in name or "expiry" in name or "pan" in name
        for name in field_names
    )


def test_multiple_payments_can_have_null_gateway_order_ids(statement):
    payments = [
        Payment.objects.create(
            statement=statement,
            amount=Decimal("100.00"),
            gateway_order_id=None,
        )
        for _ in range(2)
    ]

    assert all(payment.gateway_order_id is None for payment in payments)


def test_webhook_without_order_id_does_not_match_null_order(client, statement):
    payment = Payment.objects.create(
        statement=statement,
        amount=Decimal("100.00"),
        gateway_order_id=None,
    )

    payload = json.dumps(
        {
            "order_id": None,
            "amount": "100.00",
            "txn_id": "unexpected_transaction",
            "status": Payment.Status.SUCCESS,
        },
        separators=(",", ":"),
    )
    signature = hmac.new(
        settings.PAYMENT_WEBHOOK_SECRET.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()

    response = client.post(
        reverse("fees:webhook"),
        data=payload,
        content_type="application/json",
        HTTP_X_RAZORPAY_SIGNATURE=signature,
    )

    assert response.status_code == 404
    payment.refresh_from_db()
    statement.refresh_from_db()
    assert payment.status == Payment.Status.PENDING
    assert statement.amount_paid == Decimal("5000.00")
