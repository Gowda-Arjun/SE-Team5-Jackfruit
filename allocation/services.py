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


def create_student(
    actor,
    roll_number,
    email,
    full_name,
    gender,
    phone="",
    address="",
    guardian_name="",
    guardian_phone="",
    emergency_contact="",
):
    """Create a new student User and StudentProfile atomically with audit log."""
    from accounts.models import StudentProfile, User

    with transaction.atomic():
        user = User(
            role=User.Role.STUDENT,
            username=roll_number,
            email=email,
            roll_number=roll_number,
        )
        user.set_unusable_password()
        user.save()

        StudentProfile.objects.create(
            user=user,
            full_name=full_name,
            gender=gender,
            phone=phone,
            address=address,
            guardian_name=guardian_name,
            guardian_phone=guardian_phone,
            emergency_contact=emergency_contact,
        )

        write_audit(
            actor,
            "STUDENT_CREATED",
            user,
            details={"roll_number": roll_number, "email": email, "full_name": full_name},
        )
        return user


def update_student(
    actor,
    user,
    email,
    full_name,
    gender,
    phone="",
    address="",
    guardian_name="",
    guardian_phone="",
    emergency_contact="",
):
    """Update existing student User and StudentProfile with audit log."""
    with transaction.atomic():
        user.email = email
        user.save(update_fields=["email"])

        profile = user.profile
        profile.full_name = full_name
        profile.gender = gender
        profile.phone = phone
        profile.address = address
        profile.guardian_name = guardian_name
        profile.guardian_phone = guardian_phone
        profile.emergency_contact = emergency_contact
        profile.save()

        write_audit(
            actor,
            "STUDENT_UPDATED",
            user,
            details={"roll_number": user.roll_number, "full_name": full_name},
        )
        return user


def deactivate_student(actor, user):
    """Deactivate a student account without deleting (HMS-F-011)."""
    with transaction.atomic():
        user.is_active = False
        user.save(update_fields=["is_active"])
        write_audit(
            actor,
            "STUDENT_DEACTIVATED",
            user,
            details={"roll_number": user.roll_number},
        )
        return user
