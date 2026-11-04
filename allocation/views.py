from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import User
from core.decorators import role_required

from .forms import BlockForm, RoomForm, StudentCreateForm, StudentEditForm
from .models import Block, Room
from .services import (
    create_block,
    create_room,
    create_student,
    deactivate_room,
    deactivate_student,
    get_block_availability_summary,
    update_block,
    update_room,
    update_student,
)


@role_required(User.Role.ADMIN, User.Role.WARDEN)
def room_list(request):
    """List rooms with availability summary by block."""
    block_filter = request.GET.get("block", "")
    rooms = Room.objects.select_related("block").order_by("block__name", "floor", "number")
    if block_filter:
        rooms = rooms.filter(block__name=block_filter)

    summary = get_block_availability_summary()
    return render(
        request,
        "allocation/room_list.html",
        {
            "rooms": rooms,
            "block_summary": summary,
            "selected_block": block_filter,
            "blocks": Block.objects.all().order_by("name"),
        },
    )


@role_required(User.Role.ADMIN, User.Role.WARDEN)
def block_list(request):
    """List all blocks with per-block totals of beds, occupied and free beds."""
    summary = get_block_availability_summary()
    return render(request, "allocation/block_list.html", {"block_summary": summary})


@role_required(User.Role.ADMIN, User.Role.WARDEN)
def block_create(request):
    """Create a new block."""
    if request.method == "POST":
        form = BlockForm(request.POST)
        if form.is_valid():
            create_block(
                actor=request.user,
                name=form.cleaned_data["name"],
                gender_policy=form.cleaned_data["gender_policy"],
            )
            messages.success(request, f"Block '{form.cleaned_data['name']}' created successfully.")
            return redirect("allocation:block_list")
    else:
        form = BlockForm()
    return render(request, "allocation/block_form.html", {"form": form, "title": "Create Block"})


@role_required(User.Role.ADMIN, User.Role.WARDEN)
def block_edit(request, pk):
    """Edit an existing block."""
    block = get_object_or_404(Block, pk=pk)
    if request.method == "POST":
        form = BlockForm(request.POST, instance=block)
        if form.is_valid():
            update_block(
                actor=request.user,
                block=block,
                name=form.cleaned_data["name"],
                gender_policy=form.cleaned_data["gender_policy"],
            )
            messages.success(request, f"Block '{block.name}' updated successfully.")
            return redirect("allocation:block_list")
    else:
        form = BlockForm(instance=block)
    return render(request, "allocation/block_form.html", {"form": form, "title": f"Edit Block: {block.name}"})


@role_required(User.Role.ADMIN, User.Role.WARDEN)
def room_create(request):
    """Create a new room."""
    if request.method == "POST":
        form = RoomForm(request.POST)
        if form.is_valid():
            create_room(
                actor=request.user,
                block=form.cleaned_data["block"],
                floor=form.cleaned_data["floor"],
                number=form.cleaned_data["number"],
                room_type=form.cleaned_data["room_type"],
                capacity=form.cleaned_data["capacity"],
            )
            messages.success(request, f"Room {form.cleaned_data['number']} created successfully.")
            return redirect("allocation:room_list")
    else:
        form = RoomForm()
    return render(request, "allocation/room_form.html", {"form": form, "title": "Create Room"})


@role_required(User.Role.ADMIN, User.Role.WARDEN)
def room_edit(request, pk):
    """Edit an existing room."""
    room = get_object_or_404(Room, pk=pk)
    if request.method == "POST":
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            update_room(
                actor=request.user,
                room=room,
                block=form.cleaned_data["block"],
                floor=form.cleaned_data["floor"],
                number=form.cleaned_data["number"],
                room_type=form.cleaned_data["room_type"],
                capacity=form.cleaned_data["capacity"],
            )
            messages.success(request, f"Room {room.number} updated successfully.")
            return redirect("allocation:room_list")
    else:
        form = RoomForm(instance=room)
    return render(request, "allocation/room_form.html", {"form": form, "title": f"Edit Room: {room.number}"})


@require_POST
@role_required(User.Role.ADMIN, User.Role.WARDEN)
def room_deactivate(request, pk):
    """Deactivate a room without deleting it."""
    room = get_object_or_404(Room, pk=pk)
    deactivate_room(request.user, room)
    messages.success(request, f"Room {room.number} has been deactivated.")
    return redirect("allocation:room_list")


@role_required(User.Role.ADMIN, User.Role.WARDEN)
def student_list(request):
    """List active students with search (name / roll number) and pagination (25 per page)."""
    query = request.GET.get("q", "").strip()
    students_qs = (
        User.objects.filter(role=User.Role.STUDENT, is_active=True)
        .select_related("profile")
        .order_by("roll_number")
    )
    if query:
        students_qs = students_qs.filter(
            Q(profile__full_name__icontains=query)
            | Q(roll_number__icontains=query)
            | Q(username__icontains=query)
            | Q(email__icontains=query)
        )

    paginator = Paginator(students_qs, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "allocation/student_list.html",
        {
            "page_obj": page_obj,
            "query": query,
            "total_count": students_qs.count(),
        },
    )


@role_required(User.Role.ADMIN, User.Role.WARDEN)
def student_create(request):
    """Create a new student with profile and unusable password."""
    if request.method == "POST":
        form = StudentCreateForm(request.POST)
        if form.is_valid():
            user = create_student(
                actor=request.user,
                roll_number=form.cleaned_data["roll_number"],
                email=form.cleaned_data["email"],
                full_name=form.cleaned_data["full_name"],
                gender=form.cleaned_data["gender"],
                phone=form.cleaned_data.get("phone", ""),
                address=form.cleaned_data.get("address", ""),
                guardian_name=form.cleaned_data.get("guardian_name", ""),
                guardian_phone=form.cleaned_data.get("guardian_phone", ""),
                emergency_contact=form.cleaned_data.get("emergency_contact", ""),
            )
            messages.success(
                request,
                f"Student record created for {user.profile.full_name} ({user.roll_number}).",
            )
            return redirect("allocation:student_list")
    else:
        form = StudentCreateForm()
    return render(
        request,
        "allocation/student_form.html",
        {"form": form, "title": "Add Student Record", "is_create": True},
    )


@role_required(User.Role.ADMIN, User.Role.WARDEN)
def student_edit(request, pk):
    """Edit student details."""
    user = get_object_or_404(User, pk=pk, role=User.Role.STUDENT)
    profile = getattr(user, "profile", None)
    if request.method == "POST":
        form = StudentEditForm(request.POST, user=user)
        if form.is_valid():
            update_student(
                actor=request.user,
                user=user,
                email=form.cleaned_data["email"],
                full_name=form.cleaned_data["full_name"],
                gender=form.cleaned_data["gender"],
                phone=form.cleaned_data.get("phone", ""),
                address=form.cleaned_data.get("address", ""),
                guardian_name=form.cleaned_data.get("guardian_name", ""),
                guardian_phone=form.cleaned_data.get("guardian_phone", ""),
                emergency_contact=form.cleaned_data.get("emergency_contact", ""),
            )
            messages.success(
                request,
                f"Student record for {user.profile.full_name} updated successfully.",
            )
            return redirect("allocation:student_list")
    else:
        initial = {
            "email": user.email,
            "full_name": profile.full_name if profile else "",
            "gender": profile.gender if profile else "",
            "phone": profile.phone if profile else "",
            "address": profile.address if profile else "",
            "guardian_name": profile.guardian_name if profile else "",
            "guardian_phone": profile.guardian_phone if profile else "",
            "emergency_contact": profile.emergency_contact if profile else "",
        }
        form = StudentEditForm(initial=initial, user=user)

    return render(
        request,
        "allocation/student_form.html",
        {
            "form": form,
            "title": f"Edit Student: {user.roll_number}",
            "student_user": user,
            "is_create": False,
        },
    )


@require_POST
@role_required(User.Role.ADMIN, User.Role.WARDEN)
def student_deactivate(request, pk):
    """Deactivate a student account (sets is_active=False; never deletes)."""
    user = get_object_or_404(User, pk=pk, role=User.Role.STUDENT)
    deactivate_student(request.user, user)
    messages.success(request, f"Student {user.roll_number} has been deactivated.")
    return redirect("allocation:student_list")
