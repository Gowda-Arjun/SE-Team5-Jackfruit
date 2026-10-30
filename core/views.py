from django.apps import apps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import FieldDoesNotExist
from django.db.models import F, Sum
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone


def _get_model(app_label, model_name):
    try:
        return apps.get_model(app_label, model_name)
    except LookupError:
        return None


def get_active_allocation(student):
    allocation_model = _get_model("allocation", "Allocation")
    if allocation_model is None:
        return None

    return (
        allocation_model.objects.filter(student=student, status="ACTIVE")
        .select_related("room")
        .first()
    )


def _room_display(allocation):
    room = getattr(allocation, "room", None)
    if room is None:
        return None, None

    block = getattr(room, "block", None) or getattr(allocation, "block", None)
    block_name = None
    if block is not None:
        block_name = (
            getattr(block, "name", None)
            or getattr(block, "block_name", None)
            or str(block)
        )

    room_number = (
        getattr(room, "room_number", None)
        or getattr(room, "number", None)
        or getattr(room, "name", None)
        or str(room)
    )
    return block_name, room_number


def _number_of_roommates(allocation, student):
    allocation_model = _get_model("allocation", "Allocation")
    if allocation_model is None or getattr(allocation, "room_id", None) is None:
        return 0

    return allocation_model.objects.filter(
        room_id=allocation.room_id,
        status="ACTIVE",
    ).exclude(student=student).count()


def _get_current_fee_statement(student):
    statement_model = _get_model("fees", "FeeStatement")
    if statement_model is None:
        return None

    from fees.services import (
        CURRENT_TERM,
        NoActiveAllocation,
        NoFeeStructure,
        get_or_create_statement,
    )

    try:
        return get_or_create_statement(student, CURRENT_TERM)
    except (NoActiveAllocation, NoFeeStructure):
        return None


def _get_complaint_count(student=None, statuses=("OPEN", "IN_PROGRESS")):
    complaint_model = _get_model("complaints", "Complaint")
    if complaint_model is None:
        return 0

    complaints = complaint_model.objects.filter(status__in=statuses)
    if student is not None:
        complaints = complaints.filter(student=student)
    return complaints.count()


def _get_room_occupancy():
    room_model = _get_model("allocation", "Room")
    bed_model = _get_model("allocation", "Bed")
    allocation_model = _get_model("allocation", "Allocation")

    if room_model is None and allocation_model is not None:
        try:
            room_model = allocation_model._meta.get_field("room").remote_field.model
        except FieldDoesNotExist:
            pass

    if bed_model is not None:
        total_beds = bed_model.objects.count()
    elif room_model is not None:
        capacity_field = next(
            (
                field.name
                for field in room_model._meta.get_fields()
                if field.name in ("capacity", "bed_count", "total_beds", "beds")
                and getattr(field, "concrete", False)
            ),
            None,
        )
        if capacity_field is not None:
            total_beds = (
                room_model.objects.aggregate(total=Sum(capacity_field))["total"] or 0
            )
        else:
            total_beds = room_model.objects.count()
    else:
        total_beds = 0

    occupied = (
        allocation_model.objects.filter(status="ACTIVE").count()
        if allocation_model is not None
        else 0
    )
    vacant = max(total_beds - occupied, 0)
    occupancy_percent = round(occupied / total_beds * 100, 1) if total_beds else 0
    return {
        "total_beds": total_beds,
        "occupied_beds": occupied,
        "vacant_beds": vacant,
        "occupancy_percent": occupancy_percent,
    }


def _get_pending_room_change_count():
    allocation_app = (
        apps.get_app_config("allocation")
        if apps.is_installed("allocation")
        else None
    )
    if allocation_app is None:
        return 0

    for model in allocation_app.get_models():
        if model.__name__.lower() not in ("roomchangerequest", "roomchange"):
            continue
        try:
            model._meta.get_field("status")
        except FieldDoesNotExist:
            continue
        return model.objects.filter(status="PENDING").count()
    return 0


def _get_overdue_student_count():
    statement_model = _get_model("fees", "FeeStatement")
    if statement_model is None:
        return 0

    return (
        statement_model.objects.filter(
            due_date__lt=timezone.localdate(),
            amount_due__gt=F("amount_paid"),
        )
        .values("student_id")
        .distinct()
        .count()
    )


@login_required
def home(request):
    """Role-aware landing page: student dashboard or warden/admin dashboard."""
    if request.user.is_student:
        allocation = get_active_allocation(request.user)
        block_name, room = (
            _room_display(allocation) if allocation is not None else (None, None)
        )
        statement = _get_current_fee_statement(request.user)
        return render(
            request,
            "core/student_dashboard.html",
            {
                "allocation": allocation,
                "block_name": block_name,
                "room": room,
                "roommate_count": (
                    _number_of_roommates(allocation, request.user)
                    if allocation is not None
                    else 0
                ),
                "fee_statement": statement,
                "fee_balance": (
                    statement.amount_due - statement.amount_paid
                    if statement is not None
                    else None
                ),
                "complaint_count": _get_complaint_count(request.user),
            },
        )

    context = _get_room_occupancy()
    context.update(
        {
            "pending_room_change_count": _get_pending_room_change_count(),
            "open_complaint_count": _get_complaint_count(statuses=("OPEN",)),
            "overdue_student_count": _get_overdue_student_count(),
        }
    )
    return render(request, "core/admin_dashboard.html", context)


def healthz(request):
    """Lightweight health check for uptime monitoring (HMS-NF-002)."""
    return JsonResponse({"status": "ok"})
