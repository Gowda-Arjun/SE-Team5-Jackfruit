import pytest
from django.db import IntegrityError, transaction
from django.urls import reverse

from accounts.models import StudentProfile, User
from allocation.models import Allocation, Block, Room, RoomChangeRequest
from allocation.services import (
    DuplicatePendingRequest,
    InvalidRequestState,
    allocate_room,
    approve_room_change_request,
    create_room_change_request,
    reject_room_change_request,
)
from audit.models import AuditLog


@pytest.fixture
def admin_user():
    return User.objects.create_user(
        username="admin_user",
        email="admin_rc@example.com",
        password="password123",
        role=User.Role.ADMIN,
    )


@pytest.fixture
def warden_user():
    return User.objects.create_user(
        username="warden_user",
        email="warden_rc@example.com",
        password="password123",
        role=User.Role.WARDEN,
    )


@pytest.fixture
def male_block():
    return Block.objects.create(name="Block A", gender_policy=Block.GenderPolicy.MALE)


@pytest.fixture
def female_block():
    return Block.objects.create(name="Block B", gender_policy=Block.GenderPolicy.FEMALE)


@pytest.fixture
def male_student(male_block):
    student = User.objects.create_user(
        username="std_male",
        roll_number="CS201",
        email="std_male@example.com",
        password="password123",
        role=User.Role.STUDENT,
    )
    StudentProfile.objects.create(user=student, full_name="Student Male", gender="M")
    return student


@pytest.fixture
def current_room(male_block):
    return Room.objects.create(
        block=male_block,
        floor=1,
        number="101",
        room_type=Room.RoomType.SINGLE,
        capacity=1,
        occupancy=0,
        is_active=True,
    )


@pytest.fixture
def preferred_room(male_block):
    return Room.objects.create(
        block=male_block,
        floor=2,
        number="201",
        room_type=Room.RoomType.SINGLE,
        capacity=1,
        occupancy=0,
        is_active=True,
    )


@pytest.fixture
def active_allocation(male_student, current_room, admin_user):
    return allocate_room(male_student, current_room, admin_user)


@pytest.mark.django_db
def test_submit_room_change_request_success(client, male_student, active_allocation, preferred_room):
    """TC-Alloc-04: Student submits a valid room change request."""
    client.force_login(male_student)
    url = reverse("allocation:room_change_request")

    response = client.get(url)
    assert response.status_code == 200

    post_data = {
        "preferred_room": preferred_room.pk,
        "reason": "Want a room on a quieter floor.",
    }
    post_response = client.post(url, post_data)
    assert post_response.status_code == 302
    assert post_response.url == url

    req = RoomChangeRequest.objects.get(student=male_student)
    assert req.status == RoomChangeRequest.Status.PENDING
    assert req.current_room == active_allocation.room
    assert req.preferred_room == preferred_room
    assert req.reason == "Want a room on a quieter floor."
    assert req.decided_by is None
    assert req.decided_at is None


@pytest.mark.django_db
def test_submit_without_active_allocation_fails(client, male_student, preferred_room):
    """TC-Alloc-04: Student without an active allocation cannot submit."""
    client.force_login(male_student)
    url = reverse("allocation:room_change_request")

    post_data = {
        "preferred_room": preferred_room.pk,
        "reason": "Please give me a room.",
    }
    response = client.post(url, post_data)
    assert response.status_code == 302
    assert not RoomChangeRequest.objects.filter(student=male_student).exists()


@pytest.mark.django_db
def test_duplicate_pending_request_refused(client, male_student, active_allocation, preferred_room):
    """TC-Alloc-04: Only one PENDING request allowed per student."""
    create_room_change_request(male_student, "Initial request", preferred_room)

    # Service layer raises DuplicatePendingRequest
    with pytest.raises(DuplicatePendingRequest):
        create_room_change_request(male_student, "Second request", preferred_room)

    # Database constraint enforces uniqueness
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            RoomChangeRequest.objects.create(
                student=male_student,
                current_room=active_allocation.room,
                preferred_room=preferred_room,
                reason="Direct insert duplicate",
                status=RoomChangeRequest.Status.PENDING,
            )

    # View rejects duplicate submission
    client.force_login(male_student)
    url = reverse("allocation:room_change_request")
    response = client.post(url, {"preferred_room": preferred_room.pk, "reason": "Another request"})
    assert response.status_code == 302
    assert RoomChangeRequest.objects.filter(student=male_student).count() == 1


@pytest.mark.django_db
def test_student_sees_request_status(client, male_student, active_allocation, preferred_room):
    """TC-Alloc-04: Student can view their request status (Pending, Approved, Rejected)."""
    req = create_room_change_request(male_student, "Need ground floor", preferred_room)
    assert req.status == RoomChangeRequest.Status.PENDING

    client.force_login(male_student)
    url = reverse("allocation:room_change_request")
    resp = client.get(url)
    assert resp.status_code == 200
    assert "Pending Request in Progress" in resp.content.decode()
    assert "Need ground floor" in resp.content.decode()


@pytest.mark.django_db
def test_queue_access_control(client, male_student, warden_user, admin_user):
    """Student cannot access the change queue (403), while staff can access (200)."""
    url = reverse("allocation:room_change_queue")

    client.force_login(male_student)
    assert client.get(url).status_code == 403

    client.force_login(warden_user)
    assert client.get(url).status_code == 200

    client.force_login(admin_user)
    assert client.get(url).status_code == 200


@pytest.mark.django_db
def test_approve_room_change_moves_student(
    client, admin_user, male_student, active_allocation, current_room, preferred_room
):
    """TC-Alloc-04: Approve reallocates the student, adjusts occupancies, logs audit."""
    req = create_room_change_request(male_student, "Want room 201", preferred_room)

    current_room.refresh_from_db()
    assert current_room.occupancy == 1
    assert preferred_room.occupancy == 0

    client.force_login(admin_user)
    url = reverse("allocation:room_change_queue")
    resp = client.post(url, {"request_id": req.pk, "action": "approve"})
    assert resp.status_code == 302

    req.refresh_from_db()
    assert req.status == RoomChangeRequest.Status.APPROVED
    assert req.decided_by == admin_user
    assert req.decided_at is not None

    # Check student is moved
    current_room.refresh_from_db()
    preferred_room.refresh_from_db()
    assert current_room.occupancy == 0
    assert preferred_room.occupancy == 1

    active_alloc = Allocation.objects.get(student=male_student, status=Allocation.Status.ACTIVE)
    assert active_alloc.room == preferred_room

    old_alloc = Allocation.objects.get(pk=active_allocation.pk)
    assert old_alloc.status == Allocation.Status.ENDED

    # Audit log check
    audit_entry = AuditLog.objects.filter(action="ROOM_CHANGE_APPROVED", target_id=str(req.pk)).first()
    assert audit_entry is not None
    assert audit_entry.actor == admin_user


@pytest.mark.django_db
def test_approve_into_full_room_fails_cleanly(
    client, admin_user, male_student, active_allocation, current_room, preferred_room
):
    """TC-Alloc-04: Approving into a full room fails cleanly, request stays PENDING."""
    # Fill the preferred room
    preferred_room.occupancy = preferred_room.capacity
    preferred_room.save()

    req = create_room_change_request(male_student, "Prefer room 201", preferred_room)

    client.force_login(admin_user)
    url = reverse("allocation:room_change_queue")
    resp = client.post(url, {"request_id": req.pk, "action": "approve"}, follow=True)

    assert resp.status_code == 200
    assert "This room has no free beds. Choose another room." in resp.content.decode()

    req.refresh_from_db()
    assert req.status == RoomChangeRequest.Status.PENDING
    assert req.decided_by is None
    assert req.decided_at is None

    # Original allocation intact
    active_alloc = Allocation.objects.get(student=male_student, status=Allocation.Status.ACTIVE)
    assert active_alloc.room == current_room


@pytest.mark.django_db
def test_reject_room_change_request(
    client, admin_user, male_student, active_allocation, current_room, preferred_room
):
    """TC-Alloc-04: Reject marks request REJECTED, allocation stays intact, logs audit."""
    req = create_room_change_request(male_student, "Prefer another room", preferred_room)

    client.force_login(admin_user)
    url = reverse("allocation:room_change_queue")
    resp = client.post(url, {"request_id": req.pk, "action": "reject"})
    assert resp.status_code == 302

    req.refresh_from_db()
    assert req.status == RoomChangeRequest.Status.REJECTED
    assert req.decided_by == admin_user
    assert req.decided_at is not None

    # Allocation unchanged
    active_alloc = Allocation.objects.get(student=male_student, status=Allocation.Status.ACTIVE)
    assert active_alloc.room == current_room

    # Audit check
    audit_entry = AuditLog.objects.filter(action="ROOM_CHANGE_REJECTED", target_id=str(req.pk)).first()
    assert audit_entry is not None
    assert audit_entry.actor == admin_user


@pytest.mark.django_db
def test_cannot_decide_non_pending_request(admin_user, male_student, active_allocation, preferred_room):
    """Only PENDING requests can be decided."""
    req = create_room_change_request(male_student, "Reason", preferred_room)
    reject_room_change_request(admin_user, req.pk)

    with pytest.raises(InvalidRequestState):
        approve_room_change_request(admin_user, req.pk)

    with pytest.raises(InvalidRequestState):
        reject_room_change_request(admin_user, req.pk)
