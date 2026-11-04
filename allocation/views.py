from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import User
from core.decorators import role_required

from .forms import BlockForm, RoomForm
from .models import Block, Room
from .services import (
    create_block,
    create_room,
    deactivate_room,
    get_block_availability_summary,
    update_block,
    update_room,
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
