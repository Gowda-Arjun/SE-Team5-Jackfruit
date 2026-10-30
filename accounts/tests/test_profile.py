import pytest
from django.urls import reverse
from accounts.models import User, StudentProfile


@pytest.fixture
def student(db):
    user = User.objects.create_user(
        username="profile_student",
        email="profile_student@pes.edu",
        password="test-password",
        role=User.Role.STUDENT,
    )
    StudentProfile.objects.create(
        user=user,
        full_name="Test Student",
        gender=StudentProfile.Gender.OTHER,
        phone="9000000001",
    )
    return user


@pytest.mark.django_db
def test_student_can_update_own_profile(client, student):
    client.force_login(student)

    response = client.post(
        reverse("accounts:profile"),
        {
            "phone": "9876543210",
            "address": "Bengaluru",
            "guardian_name": "Test Guardian",
            "guardian_phone": "9876543211",
            "emergency_contact": "9876543212",
        },
    )

    assert response.status_code == 302

    student.profile.refresh_from_db()
    assert student.profile.phone == "9876543210"
    assert student.profile.address == "Bengaluru"


@pytest.mark.django_db
def test_unauthenticated_user_cannot_access_profile(client):
    response = client.get(reverse("accounts:profile"))

    assert response.status_code == 302
    assert "/accounts/login/" in response.url


@pytest.mark.django_db
def test_student_can_only_update_own_profile(client, student):
    another = User.objects.create_user(
        username="another_student",
        email="another@pes.edu",
        password="test-password",
        role=User.Role.STUDENT,
    )
    StudentProfile.objects.create(
        user=another,
        full_name="Another Student",
        gender=StudentProfile.Gender.OTHER,
        phone="9000000002",
    )

    client.force_login(student)

    client.post(
        reverse("accounts:profile"),
        {
            "phone": "9999999999",
            "address": "Test Address",
            "guardian_name": "Test Guardian",
            "guardian_phone": "9876543211",
            "emergency_contact": "9876543212",
        },
    )

    another.profile.refresh_from_db()
    assert another.profile.phone == "9000000002"
