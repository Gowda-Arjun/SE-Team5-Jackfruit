from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import User
from audit.services import write_audit
from core.decorators import role_required

from .forms import FeeStructureForm
from .models import FeeStructure


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
