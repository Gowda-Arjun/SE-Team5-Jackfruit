from datetime import date
from decimal import Decimal, InvalidOperation

from django.apps import apps

from reports.services import defaulters_report

from .models import FeeStatement, FeeStructure, Payment

CURRENT_TERM = "2026-ODD"


class NoFeeStructure(Exception):
    """No fee structure is configured for a term and room type."""


class NoActiveAllocation(Exception):
    """The student does not have an active room allocation."""


def get_active_allocation(student):
    try:
        allocation_model = apps.get_model("allocation", "Allocation")
    except LookupError:
        return None

    return (
        allocation_model.objects.filter(student=student, status="ACTIVE")
        .select_related("room")
        .first()
    )


def get_or_create_statement(student, term):
    statement = FeeStatement.objects.filter(student=student, term=term).first()
    if statement is not None:
        return statement

    allocation = get_active_allocation(student)
    if allocation is None:
        raise NoActiveAllocation

    room_type = allocation.room.room_type
    try:
        structure = FeeStructure.objects.get(term=term, room_type=room_type)
    except FeeStructure.DoesNotExist as exc:
        raise NoFeeStructure(
            f"No fee structure for term {term} and room type {room_type}."
        ) from exc

    statement, _ = FeeStatement.objects.get_or_create(
        student=student,
        term=term,
        defaults={
            "amount_due": structure.amount,
            "due_date": structure.due_date,
        },
    )
    return statement


def reconcile_payments(date_from, date_to, ledger):
    """Compare successful payments in a date range with normalized gateway ledger rows."""
    ledger_by_order = {
        entry.get("order_id"): entry
        for entry in ledger
        if isinstance(entry, dict) and entry.get("order_id")
    }
    payments = (
        Payment.objects.filter(
            status=Payment.Status.SUCCESS,
            created_at__date__gte=date_from,
            created_at__date__lte=date_to,
        )
        .select_related("statement__student")
        .order_by("created_at", "pk")
    )
    matched_count = 0
    mismatches = []
    for payment in payments:
        entry = ledger_by_order.get(payment.gateway_order_id)
        reason = None
        if entry is None:
            reason = "Missing from gateway ledger"
        else:
            try:
                ledger_amount = Decimal(str(entry["amount"])) / 100
            except (KeyError, InvalidOperation, TypeError, ValueError):
                ledger_amount = None
            ledger_status = str(entry.get("status", "")).lower()
            if ledger_amount != payment.amount:
                reason = "Amount differs"
            elif ledger_status not in ("captured", "success"):
                reason = "Status differs"

        if reason is None:
            matched_count += 1
            continue

        mismatches.append(
            {
                "payment": payment,
                "ledger_amount": ledger_amount if entry else None,
                "ledger_status": entry.get("status", "Missing")
                if entry
                else "Missing",
                "reason": reason,
            }
        )

    today = date.today()
    defaulters = defaulters_report(date.min, today)["rows"]
    return {
        "matched_count": matched_count,
        "mismatches": mismatches,
        "defaulters": [
            {
                "student": row[0],
                "roll_number": row[1],
                "term": row[2],
                "balance": row[5],
                "due_date": row[6],
            }
            for row in defaulters
        ],
    }
