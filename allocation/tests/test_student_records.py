import pytest
from django.urls import reverse

from accounts.models import StudentProfile, User
from audit.models import AuditLog


@pytest.fixture
def admin_user():
    return User.objects.create_user(
        username="admin_user",
        email="admin_user@example.com",
        password="password123",
        role=User.Role.ADMIN,
    )


@pytest.fixture
def student_user():
    user = User.objects.create_user(
        username="STD999",
        roll_number="STD999",
        email="std999@example.com",
        password="password123",
        role=User.Role.STUDENT,
    )
    StudentProfile.objects.create(
        user=user,
        full_name="Existing Student",
        gender="M",
    )
    return user


@pytest.mark.django_db
def test_create_student_appears_in_list(client, admin_user):
    client.force_login(admin_user)
    resp = client.post(
        reverse("allocation:student_create"),
        {
            "roll_number": "STD101",
            "email": "std101@example.com",
            "full_name": "Alice Wonder",
            "gender": "F",
            "phone": "9876543210",
            "address": "123 Campus Road",
            "guardian_name": "Bob Wonder",
            "guardian_phone": "9876543211",
            "emergency_contact": "Emergency Bob",
        },
    )
    assert resp.status_code == 302
    created_user = User.objects.get(roll_number="STD101")
    assert created_user.role == User.Role.STUDENT
    assert created_user.profile.full_name == "Alice Wonder"
    assert created_user.profile.gender == "F"
    assert not created_user.has_usable_password()

    # Check appears in list
    list_resp = client.get(reverse("allocation:student_list"))
    assert list_resp.status_code == 200
    assert "STD101" in list_resp.content.decode()
    assert "Alice Wonder" in list_resp.content.decode()

    # Check audit log
    audit = AuditLog.objects.filter(action="STUDENT_CREATED", target_id=str(created_user.pk)).first()
    assert audit is not None
    assert audit.actor == admin_user


@pytest.mark.django_db
def test_edit_student_persists(client, admin_user, student_user):
    client.force_login(admin_user)
    resp = client.post(
        reverse("allocation:student_edit", kwargs={"pk": student_user.pk}),
        {
            "email": "updated_email@example.com",
            "full_name": "Updated Name",
            "gender": "M",
            "phone": "9998887776",
            "address": "New Address",
            "guardian_name": "New Guardian",
            "guardian_phone": "9998887777",
            "emergency_contact": "New Emergency",
        },
    )
    assert resp.status_code == 302
    student_user.refresh_from_db()
    student_user.profile.refresh_from_db()
    assert student_user.email == "updated_email@example.com"
    assert student_user.profile.full_name == "Updated Name"

    # Check audit log
    assert AuditLog.objects.filter(action="STUDENT_UPDATED", target_id=str(student_user.pk)).exists()


@pytest.mark.django_db
def test_deactivate_hides_student_from_list_and_blocks_login(client, admin_user):
    # Create student with usable password for testing login block
    user = User.objects.create_user(
        username="DEACT01",
        roll_number="DEACT01",
        email="deact01@example.com",
        password="knownpassword",
        role=User.Role.STUDENT,
    )
    StudentProfile.objects.create(user=user, full_name="Deact User", gender="M")

    # Verify user can log in before deactivation
    assert client.login(username="DEACT01", password="knownpassword")
    client.logout()

    # Deactivate as admin
    client.force_login(admin_user)
    resp = client.post(reverse("allocation:student_deactivate", kwargs={"pk": user.pk}))
    assert resp.status_code == 302
    user.refresh_from_db()
    assert user.is_active is False

    # Check hidden from active student list
    list_resp = client.get(reverse("allocation:student_list"))
    assert user not in list_resp.context["page_obj"].object_list

    # Verify cannot log in anymore
    client.logout()
    assert not client.login(username="DEACT01", password="knownpassword")

    # Verify user was NOT deleted (SAD / HMS-F-011 rule)
    assert User.objects.filter(pk=user.pk).exists()
    assert AuditLog.objects.filter(action="STUDENT_DEACTIVATED", target_id=str(user.pk)).exists()


@pytest.mark.django_db
def test_student_role_gets_403(client, student_user):
    client.force_login(student_user)
    urls = [
        reverse("allocation:student_list"),
        reverse("allocation:student_create"),
        reverse("allocation:student_edit", kwargs={"pk": student_user.pk}),
    ]
    for url in urls:
        resp = client.get(url)
        assert resp.status_code == 403
