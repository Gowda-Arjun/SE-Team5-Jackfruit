from django.apps import apps

from .models import FeeStatement, FeeStructure

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
