import pytest
from django.db import IntegrityError, transaction
from django.urls import reverse

from accounts.models import User
from audit.models import AuditLog
from allocation.models import Block, Room


@pytest.fixture
def admin_user():
    return User.objects.create_user(
        username="test_admin",
        email="test_admin@example.com",
        password="password123",
        role=User.Role.ADMIN,
    )


@pytest.fixture
def warden_user():
    return User.objects.create_user(
        username="test_warden",
        email="test_warden@example.com",
        password="password123",
        role=User.Role.WARDEN,
    )


@pytest.fixture
def student_user():
    return User.objects.create_user(
        username="test_student",
        email="test_student@example.com",
        password="password123",
        role=User.Role.STUDENT,
    )


@pytest.fixture
def sample_block():
    return Block.objects.create(name="Block Alpha", gender_policy="M")


@pytest.mark.django_db
def test_create_and_edit_room(client, admin_user, sample_block):
    client.force_login(admin_user)

    # Create room
    create_url = reverse("allocation:room_create")
    resp = client.post(
        create_url,
        {
            "block": sample_block.pk,
            "floor": 2,
            "number": "A-201",
            "room_type": "SINGLE",
            "capacity": 1,
        },
    )
    assert resp.status_code == 302
    room = Room.objects.get(number="A-201")
    assert room.block == sample_block
    assert room.capacity == 1
    assert room.is_active is True

    # Audit log check
    audit = AuditLog.objects.filter(action="ROOM_CREATED", target_id=str(room.pk)).first()
    assert audit is not None
    assert audit.actor == admin_user

    # Edit room
    edit_url = reverse("allocation:room_edit", kwargs={"pk": room.pk})
    resp = client.post(
        edit_url,
        {
            "block": sample_block.pk,
            "floor": 2,
            "number": "A-201",
            "room_type": "SHARED",
            "capacity": 2,
        },
    )
    assert resp.status_code == 302
    room.refresh_from_db()
    assert room.room_type == "SHARED"
    assert room.capacity == 2

    # Audit log for update
    assert AuditLog.objects.filter(action="ROOM_UPDATED", target_id=str(room.pk)).exists()


@pytest.mark.django_db
def test_duplicate_room_number_in_same_block_rejected(client, admin_user, sample_block):
    Room.objects.create(
        block=sample_block,
        floor=1,
        number="A-101",
        room_type="SINGLE",
        capacity=1,
    )

    client.force_login(admin_user)
    resp = client.post(
        reverse("allocation:room_create"),
        {
            "block": sample_block.pk,
            "floor": 1,
            "number": "A-101",
            "room_type": "SINGLE",
            "capacity": 1,
        },
    )
    assert resp.status_code == 200
    assert "A room with this number already exists in this block." in resp.content.decode()

    # DB level unique constraint
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Room.objects.create(
                block=sample_block,
                floor=1,
                number="A-101",
                room_type="SHARED",
                capacity=2,
            )


@pytest.mark.django_db
def test_capacity_less_than_occupancy_rejected_by_db_constraint(sample_block):
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Room.objects.create(
                block=sample_block,
                floor=1,
                number="A-102",
                room_type="SINGLE",
                capacity=1,
                occupancy=2,  # occupancy > capacity
            )


@pytest.mark.django_db
def test_student_gets_403_on_admin_pages(client, student_user, sample_block):
    client.force_login(student_user)

    urls = [
        reverse("allocation:room_list"),
        reverse("allocation:room_create"),
        reverse("allocation:block_list"),
        reverse("allocation:block_create"),
    ]
    for url in urls:
        resp = client.get(url)
        assert resp.status_code == 403


@pytest.mark.django_db
def test_room_deactivation(client, warden_user, sample_block):
    client.force_login(warden_user)
    room = Room.objects.create(
        block=sample_block,
        floor=1,
        number="A-103",
        room_type="SINGLE",
        capacity=1,
    )
    deactivate_url = reverse("allocation:room_deactivate", kwargs={"pk": room.pk})
    resp = client.post(deactivate_url)
    assert resp.status_code == 302
    room.refresh_from_db()
    assert room.is_active is False
    assert AuditLog.objects.filter(action="ROOM_DEACTIVATED", target_id=str(room.pk)).exists()


@pytest.mark.django_db
def test_availability_counts_in_room_list(client, admin_user, sample_block):
    client.force_login(admin_user)
    Room.objects.create(
        block=sample_block,
        floor=1,
        number="A-104",
        room_type="SHARED",
        capacity=2,
        occupancy=1,
    )
    resp = client.get(reverse("allocation:room_list"))
    assert resp.status_code == 200
    content = resp.content.decode()
    assert "Block Alpha" in content
    assert "A-104" in content
