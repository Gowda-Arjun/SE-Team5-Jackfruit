import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from accounts.models import User
from complaints.models import Complaint
from complaints.services import raise_complaint

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


@pytest.fixture(autouse=True)
def media_in_tmp(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path


@pytest.fixture
def student(db):
    return User.objects.create_user("stu1", email="stu1@pes.edu", password="Str0ng!pass", roll_number="PES1")


@pytest.fixture
def student_client(client, student):
    client.force_login(student)
    return client


def post_complaint(client, **extra):
    data = {"category": "PLUMBING", "description": "Tap in room 101 is leaking"}
    data.update(extra)
    return client.post(reverse("complaints:create"), data)


def test_raise_complaint_creates_open_ticket(student_client, student):
    """TC-Maint-01 / AC-F-030: unique ticket id and status Open."""
    resp = post_complaint(student_client)
    assert resp.status_code == 302
    complaint = Complaint.objects.get()
    assert complaint.student == student
    assert complaint.status == Complaint.Status.OPEN
    assert complaint.ticket_id == f"CMP-{complaint.pk:06d}"


def test_ticket_ids_are_unique(student):
    ids = {raise_complaint(student, "OTHER", f"issue {i}").ticket_id for i in range(5)}
    assert len(ids) == 5


def test_valid_photo_is_stored_with_random_name(student_client):
    photo = SimpleUploadedFile("leak.PNG", PNG_BYTES, content_type="image/png")
    assert post_complaint(student_client, photo=photo).status_code == 302
    stored = Complaint.objects.get().photo.name
    assert stored.startswith("complaints/") and stored.endswith(".png") and "leak" not in stored


@pytest.mark.parametrize(
    "name,content,content_type",
    [
        ("evil.php", b"<?php system($_GET['c']); ?>", "application/x-php"),   # wrong extension
        ("evil.png", b"<?php system($_GET['c']); ?>", "image/png"),           # renamed script
        ("doc.png", PNG_BYTES, "application/pdf"),                            # wrong declared type
    ],
)
def test_unsafe_uploads_rejected(student_client, name, content, content_type):
    """TC-Sec-09: file-upload safety."""
    resp = post_complaint(student_client, photo=SimpleUploadedFile(name, content, content_type=content_type))
    assert resp.status_code == 200
    assert "not allowed" in resp.content.decode()
    assert not Complaint.objects.exists()


def test_oversized_photo_rejected(student_client):
    big = SimpleUploadedFile("big.png", PNG_BYTES + b"\x00" * (5 * 1024 * 1024), content_type="image/png")
    assert "not allowed" in post_complaint(student_client, photo=big).content.decode()


def test_missing_fields_show_errors(student_client):
    resp = student_client.post(reverse("complaints:create"), {"category": "", "description": ""})
    assert resp.status_code == 200 and not Complaint.objects.exists()


def test_student_sees_only_own_complaints(student_client, student):
    other = User.objects.create_user("stu2", email="stu2@pes.edu", password="Str0ng!pass")
    mine = raise_complaint(student, "ELECTRICAL", "Fan not working")
    theirs = raise_complaint(other, "CLEANING", "Corridor not cleaned")
    page = student_client.get(reverse("complaints:my_complaints")).content.decode()
    assert mine.ticket_id in page and theirs.ticket_id not in page


def test_admin_cannot_use_student_complaint_form(client, db):
    admin = User.objects.create_user("adm", email="adm@pes.edu", password="Str0ng!pass", role=User.Role.ADMIN)
    client.force_login(admin)
    assert client.get(reverse("complaints:create")).status_code == 403


def test_anonymous_redirected_to_login(client, db):
    resp = client.get(reverse("complaints:create"))
    assert resp.status_code == 302 and reverse("accounts:login") in resp.url
