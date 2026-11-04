import pytest
from django.urls import reverse

from accounts.models import StudentProfile, User
from allocation.models import Allocation, Block, Room


@pytest.fixture
def admin_user():
    return User.objects.create_user(
        username="admin_user",
        email="admin_user@test.com",
        password="password123",
        role=User.Role.ADMIN,
    )


@pytest.fixture
def male_block():
    return Block.objects.create(name="Block C", gender_policy="M")


@pytest.fixture
def student_1():
    u = User.objects.create_user(
        username="student1",
        roll_number="ST01",
        email="st01@test.com",
        password="password123",
        role=User.Role.STUDENT,
    )
    StudentProfile.objects.create(user=u, full_name="Student One", gender="M")
    return u


@pytest.fixture
def student_2():
    u = User.objects.create_user(
        username="student2",
        roll_number="ST02",
        email="st02@test.com",
        password="password123",
        role=User.Role.STUDENT,
    )
    StudentProfile.objects.create(user=u, full_name="Student Two", gender="M")
    return u


@pytest.fixture
def student_3_other_room():
    u = User.objects.create_user(
        username="student3",
        roll_number="ST03",
        email="st03@test.com",
        password="password123",
        role=User.Role.STUDENT,
    )
    StudentProfile.objects.create(user=u, full_name="Student Three", gender="M")
    return u


@pytest.mark.django_db
def test_student_views_own_room_and_roommates(client, male_block, student_1, student_2, student_3_other_room):
    shared_room = Room.objects.create(
        block=male_block,
        floor=2,
        number="C-201",
        room_type="SHARED",
        capacity=2,
        occupancy=2,
    )
    other_room = Room.objects.create(
        block=male_block,
        floor=3,
        number="C-301",
        room_type="SINGLE",
        capacity=1,
        occupancy=1,
    )

    Allocation.objects.create(student=student_1, room=shared_room, status=Allocation.Status.ACTIVE)
    Allocation.objects.create(student=student_2, room=shared_room, status=Allocation.Status.ACTIVE)
    Allocation.objects.create(student=student_3_other_room, room=other_room, status=Allocation.Status.ACTIVE)

    # Student 1 logs in
    client.force_login(student_1)
    resp = client.get(reverse("allocation:my_room"))
    assert resp.status_code == 200
    content = resp.content.decode()

    # Shows own room details
    assert "Block C" in content
    assert "C-201" in content
    assert "Shared" in content

    # Shows roommate (Student Two)
    assert "Student Two" in content

    # Does NOT show another student from another room
    assert "C-301" not in content
    assert "Student Three" not in content


@pytest.mark.django_db
def test_student_without_allocation_sees_message(client, student_1):
    client.force_login(student_1)
    resp = client.get(reverse("allocation:my_room"))
    assert resp.status_code == 200
    assert "You have not been allocated a room yet." in resp.content.decode()


@pytest.mark.django_db
def test_admin_gets_403_on_my_room(client, admin_user):
    client.force_login(admin_user)
    resp = client.get(reverse("allocation:my_room"))
    assert resp.status_code == 403
