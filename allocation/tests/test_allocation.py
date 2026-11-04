import pytest
from django.db import IntegrityError, transaction
from django.urls import reverse

from accounts.models import StudentProfile, User
from audit.models import AuditLog
from allocation.models import Allocation, Block, Room
from allocation.services import (
    GenderPolicyMismatch,
    RoomFull,
    RoomInactive,
    allocate_room,
)


@pytest.fixture
def admin_user():
    return User.objects.create_user(
        username="admin_user",
        email="admin_alloc@example.com",
        password="password123",
        role=User.Role.ADMIN,
    )


@pytest.fixture
def male_student():
    u = User.objects.create_user(
        username="male_std",
        roll_number="M101",
        email="male@example.com",
        password="password123",
        role=User.Role.STUDENT,
    )
    StudentProfile.objects.create(user=u, full_name="Male Student", gender="M")
    return u


@pytest.fixture
def female_student():
    u = User.objects.create_user(
        username="female_std",
        roll_number="F101",
        email="female@example.com",
        password="password123",
        role=User.Role.STUDENT,
    )
    StudentProfile.objects.create(user=u, full_name="Female Student", gender="F")
    return u


@pytest.fixture
def male_block():
    return Block.objects.create(name="Block Men", gender_policy="M")


@pytest.fixture
def female_block():
    return Block.objects.create(name="Block Women", gender_policy="F")


@pytest.mark.django_db
def test_boundaries_n_minus_1_n_n_plus_1_occupancy(admin_user, male_block):
    """Room with capacity 2: N-1 (1st allocation), N (2nd allocation), N+1 (3rd allocation rejected)."""
    room = Room.objects.create(
        block=male_block,
        floor=1,
        number="M101",
        room_type="SHARED",
        capacity=2,
        occupancy=0,
    )

    s1 = User.objects.create_user(username="s1", roll_number="S1", email="s1@test.com", role=User.Role.STUDENT)
    StudentProfile.objects.create(user=s1, full_name="S1", gender="M")

    s2 = User.objects.create_user(username="s2", roll_number="S2", email="s2@test.com", role=User.Role.STUDENT)
    StudentProfile.objects.create(user=s2, full_name="S2", gender="M")

    s3 = User.objects.create_user(username="s3", roll_number="S3", email="s3@test.com", role=User.Role.STUDENT)
    StudentProfile.objects.create(user=s3, full_name="S3", gender="M")

    # N-1 = 1: First allocation succeeds
    a1 = allocate_room(s1, room, actor=admin_user)
    assert a1.status == Allocation.Status.ACTIVE
    room.refresh_from_db()
    assert room.occupancy == 1

    # N = 2: Second allocation succeeds (room reaches capacity)
    a2 = allocate_room(s2, room, actor=admin_user)
    assert a2.status == Allocation.Status.ACTIVE
    room.refresh_from_db()
    assert room.occupancy == 2

    # N+1 = 3: Third allocation rejected with RoomFull exception
    with pytest.raises(RoomFull):
        allocate_room(s3, room, actor=admin_user)

    room.refresh_from_db()
    assert room.occupancy == 2

    # Verify audit row for denied attempt
    denied_audit = AuditLog.objects.filter(
        action="ROOM_ALLOCATED",
        outcome=AuditLog.Outcome.DENIED,
        target_id=str(room.pk),
    ).first()
    assert denied_audit is not None
    assert denied_audit.details["reason"] == "Room is full"


@pytest.mark.django_db
def test_gender_mismatch_rejected_and_logged(admin_user, male_block, female_student):
    room = Room.objects.create(
        block=male_block,
        floor=1,
        number="M102",
        room_type="SINGLE",
        capacity=1,
    )

    with pytest.raises(GenderPolicyMismatch):
        allocate_room(female_student, room, actor=admin_user)

    assert room.occupancy == 0
    denied = AuditLog.objects.filter(
        action="ROOM_ALLOCATED",
        outcome=AuditLog.Outcome.DENIED,
        target_id=str(room.pk),
    ).first()
    assert denied is not None
    assert denied.details["reason"] == "Gender policy mismatch"


@pytest.mark.django_db
def test_inactive_room_rejected_and_logged(admin_user, male_block, male_student):
    room = Room.objects.create(
        block=male_block,
        floor=1,
        number="M103",
        room_type="SINGLE",
        capacity=1,
        is_active=False,
    )

    with pytest.raises(RoomInactive):
        allocate_room(male_student, room, actor=admin_user)

    denied = AuditLog.objects.filter(
        action="ROOM_ALLOCATED",
        outcome=AuditLog.Outcome.DENIED,
        target_id=str(room.pk),
    ).first()
    assert denied is not None
    assert denied.details["reason"] == "Room is inactive"


@pytest.mark.django_db
def test_reallocation_moves_occupancy(admin_user, male_block, male_student):
    room1 = Room.objects.create(
        block=male_block,
        floor=1,
        number="M104",
        room_type="SINGLE",
        capacity=1,
        occupancy=0,
    )
    room2 = Room.objects.create(
        block=male_block,
        floor=1,
        number="M105",
        room_type="SINGLE",
        capacity=1,
        occupancy=0,
    )

    # Initial allocation to room 1
    alloc1 = allocate_room(male_student, room1, actor=admin_user)
    assert alloc1.status == Allocation.Status.ACTIVE
    room1.refresh_from_db()
    assert room1.occupancy == 1

    # Reallocation to room 2
    alloc2 = allocate_room(male_student, room2, actor=admin_user)
    assert alloc2.status == Allocation.Status.ACTIVE

    # Old allocation ended, new allocation active
    alloc1.refresh_from_db()
    assert alloc1.status == Allocation.Status.ENDED
    assert alloc1.end_date is not None

    # Room 1 occupancy decremented, Room 2 occupancy incremented
    room1.refresh_from_db()
    room2.refresh_from_db()
    assert room1.occupancy == 0
    assert room2.occupancy == 1


@pytest.mark.django_db
def test_second_active_allocation_impossible(male_block, male_student):
    room = Room.objects.create(
        block=male_block,
        floor=1,
        number="M106",
        room_type="SHARED",
        capacity=2,
    )

    Allocation.objects.create(
        student=male_student,
        room=room,
        status=Allocation.Status.ACTIVE,
    )

    # Second active allocation violates partial UniqueConstraint
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Allocation.objects.create(
                student=male_student,
                room=room,
                status=Allocation.Status.ACTIVE,
            )


@pytest.mark.django_db
def test_allocate_view_success_and_student_403(client, admin_user, male_block, male_student):
    room = Room.objects.create(
        block=male_block,
        floor=1,
        number="M107",
        room_type="SINGLE",
        capacity=1,
        occupancy=0,
    )

    # Student cannot access
    client.force_login(male_student)
    resp = client.get(reverse("allocation:allocate"))
    assert resp.status_code == 403

    # Admin access and allocate
    client.force_login(admin_user)
    resp = client.post(
        reverse("allocation:allocate"),
        {"student": male_student.pk, "room": room.pk},
    )
    assert resp.status_code == 302
    room.refresh_from_db()
    assert room.occupancy == 1
    assert Allocation.objects.filter(student=male_student, room=room, status="ACTIVE").exists()
