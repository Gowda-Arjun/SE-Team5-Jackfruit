from django.db import transaction
from django.db.models import Case, IntegerField, Sum, Value, When

from audit.services import write_audit

from .models import Block, Room


def get_block_availability_summary():
    """Return all blocks annotated with total beds, occupied beds, and free beds."""
    blocks = Block.objects.annotate(
        total_beds=Sum(
            Case(
                When(rooms__is_active=True, then="rooms__capacity"),
                default=Value(0),
                output_field=IntegerField(),
            )
        ),
        occupied_beds=Sum(
            Case(
                When(rooms__is_active=True, then="rooms__occupancy"),
                default=Value(0),
                output_field=IntegerField(),
            )
        ),
    ).order_by("name")

    summary = []
    for b in blocks:
        total = b.total_beds or 0
        occupied = b.occupied_beds or 0
        summary.append({
            "block": b,
            "total_beds": total,
            "occupied_beds": occupied,
            "free_beds": max(total - occupied, 0),
        })
    return summary


def create_block(actor, name, gender_policy):
    """Create a new hostel block with audit log entry."""
    with transaction.atomic():
        block = Block.objects.create(name=name, gender_policy=gender_policy)
        write_audit(
            actor,
            "BLOCK_CREATED",
            block,
            details={"name": block.name, "gender_policy": block.gender_policy},
        )
        return block


def update_block(actor, block, name, gender_policy):
    """Update an existing hostel block with audit log entry."""
    with transaction.atomic():
        block.name = name
        block.gender_policy = gender_policy
        block.save()
        write_audit(
            actor,
            "BLOCK_UPDATED",
            block,
            details={"name": block.name, "gender_policy": block.gender_policy},
        )
        return block


def create_room(actor, block, floor, number, room_type, capacity):
    """Create a new room in a block with audit log entry."""
    with transaction.atomic():
        room = Room.objects.create(
            block=block,
            floor=floor,
            number=number,
            room_type=room_type,
            capacity=capacity,
            occupancy=0,
            is_active=True,
        )
        write_audit(
            actor,
            "ROOM_CREATED",
            room,
            details={
                "block": block.name,
                "number": number,
                "room_type": room_type,
                "capacity": capacity,
            },
        )
        return room


def update_room(actor, room, block, floor, number, room_type, capacity):
    """Update room attributes with audit log entry."""
    with transaction.atomic():
        room.block = block
        room.floor = floor
        room.number = number
        room.room_type = room_type
        room.capacity = capacity
        room.save()
        write_audit(
            actor,
            "ROOM_UPDATED",
            room,
            details={
                "block": block.name,
                "number": number,
                "room_type": room_type,
                "capacity": capacity,
            },
        )
        return room


def deactivate_room(actor, room):
    """Deactivate a room without deleting it (soft deactivation)."""
    with transaction.atomic():
        room.is_active = False
        room.save(update_fields=["is_active"])
        write_audit(
            actor,
            "ROOM_DEACTIVATED",
            room,
            details={"block": room.block.name, "number": room.number},
        )
        return room
