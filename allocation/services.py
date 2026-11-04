import datetime

from django.db import transaction
from django.db.models import Case, IntegerField, Sum, Value, When

from audit.models import AuditLog
from audit.services import write_audit

from .models import Allocation, Block, Room


class AllocationError(Exception):
    """Base error for allocation operations."""
    pass


class RoomInactive(AllocationError):
    """Raised when room is not active."""
    pass


class GenderPolicyMismatch(AllocationError):
    """Raised when student gender does not match block policy."""
    pass


class RoomFull(AllocationError):
    """Raised when room occupancy has reached capacity."""
    pass


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


def allocate_room(student, room, actor):
    """Allocate a room to a student atomically with concurrency lock and validation (HMS-F-012, HMS-F-015)."""
    denial = None
    new_allocation = None

    with transaction.atomic():
        locked_room = Room.objects.select_for_update().select_related("block").get(pk=room.pk)

        if not locked_room.is_active:
            denial = (
                RoomInactive("This room is inactive. Choose an active room."),
                locked_room,
                {"student": student.username, "reason": "Room is inactive"},
            )
        else:
            student_gender = getattr(getattr(student, "profile", None), "gender", None)
            if locked_room.block.gender_policy != student_gender:
                denial = (
                    GenderPolicyMismatch("This block is not available for this student."),
                    locked_room,
                    {
                        "student": student.username,
                        "student_gender": student_gender,
                        "block_gender_policy": locked_room.block.gender_policy,
                        "reason": "Gender policy mismatch",
                    },
                )
            elif locked_room.occupancy >= locked_room.capacity:
                denial = (
                    RoomFull("This room has no free beds. Choose another room."),
                    locked_room,
                    {
                        "student": student.username,
                        "occupancy": locked_room.occupancy,
                        "capacity": locked_room.capacity,
                        "reason": "Room is full",
                    },
                )

        if not denial:
            old_allocation = (
                Allocation.objects.select_for_update()
                .filter(student=student, status=Allocation.Status.ACTIVE)
                .first()
            )

            today = datetime.date.today()
            if old_allocation is not None:
                old_allocation.status = Allocation.Status.ENDED
                old_allocation.end_date = today
                old_allocation.save(update_fields=["status", "end_date"])

                if old_allocation.room_id == locked_room.pk:
                    locked_room.occupancy -= 1
                else:
                    old_room = Room.objects.select_for_update().get(pk=old_allocation.room_id)
                    old_room.occupancy = max(old_room.occupancy - 1, 0)
                    old_room.save(update_fields=["occupancy"])

            new_allocation = Allocation.objects.create(
                student=student,
                room=locked_room,
                start_date=today,
                status=Allocation.Status.ACTIVE,
            )

            locked_room.occupancy += 1
            locked_room.save(update_fields=["occupancy"])

            write_audit(
                actor,
                "ROOM_ALLOCATED",
                target=new_allocation,
                outcome=AuditLog.Outcome.SUCCESS,
                details={
                    "student": student.username,
                    "room": locked_room.number,
                    "block": locked_room.block.name,
                    "is_reallocation": old_allocation is not None,
                },
            )

    if denial:
        exc, target, details = denial
        write_audit(
            actor,
            "ROOM_ALLOCATED",
            target=target,
            outcome=AuditLog.Outcome.DENIED,
            details=details,
        )
        raise exc

    return new_allocation
