from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import User
from audit.services import write_audit
from core.decorators import role_required

from .forms import FeeStructureForm
from .models import FeeStatement, FeeStructure
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
