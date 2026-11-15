import logging

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from accounts.models import User
from complaints.models import Complaint
from complaints.services import raise_complaint
from core.log_filters import MaskPIIFilter, mask_pii

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


@pytest.fixture(autouse=True)
def media_in_tmp(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path


@pytest.fixture
def owner(db):
    return User.objects.create_user("own", email="own@pes.edu", password="Str0ng!pass")


@pytest.fixture
def complaint_with_photo(owner):
    return raise_complaint(owner, "PLUMBING", "Leak", photo=SimpleUploadedFile("p.png", PNG_BYTES))


def photo_url(c):
    return reverse("complaints:photo", args=[c.ticket_id])


def test_owner_downloads_photo_as_attachment(client, owner, complaint_with_photo):
    client.force_login(owner)
    resp = client.get(photo_url(complaint_with_photo))
    assert resp.status_code == 200
    assert resp["Content-Disposition"].startswith("attachment")
    assert resp["X-Content-Type-Options"] == "nosniff"
    assert b"".join(resp.streaming_content) == PNG_BYTES


def test_other_student_cannot_download_photo(client, complaint_with_photo):
    """TC-Sec-01: IDOR attempt returns 404."""
    intruder = User.objects.create_user("intr", email="i@pes.edu", password="Str0ng!pass")
    client.force_login(intruder)
    assert client.get(photo_url(complaint_with_photo)).status_code == 404


def test_warden_can_download_photo(client, complaint_with_photo):
    warden = User.objects.create_user("w", email="w@pes.edu", password="Str0ng!pass", role=User.Role.WARDEN)
    client.force_login(warden)
    assert client.get(photo_url(complaint_with_photo)).status_code == 200


def test_unassigned_technician_cannot_download_photo(client, complaint_with_photo):
    tech = User.objects.create_user("t", email="t@pes.edu", password="Str0ng!pass", role=User.Role.TECHNICIAN)
    client.force_login(tech)
    assert client.get(photo_url(complaint_with_photo)).status_code == 404


def test_no_photo_is_404(client, owner):
    c = raise_complaint(owner, "OTHER", "No photo")
    client.force_login(owner)
    assert client.get(photo_url(c)).status_code == 404


def test_photo_not_reachable_via_public_media_url(client, complaint_with_photo):
    """Uploads are not served from a public /media/ URL."""
    assert client.get("/media/" + complaint_with_photo.photo.name).status_code == 404


@pytest.mark.parametrize("raw,masked", [
    ("login failed for stu1@pes.edu", "login failed for s***@pes.edu"),
    ("call 9876543210 now", "call ******3210 now"),
    ("guardian +91 9876543210", "guardian ******3210"),
    ("ticket CMP-000123 updated", "ticket CMP-000123 updated"),   # ids are untouched
])
def test_mask_pii(raw, masked):
    assert mask_pii(raw) == masked


def test_log_records_are_masked():
    record = logging.LogRecord("hms", logging.INFO, __file__, 1, "user %s phone %s", ("a.b@pes.edu", "9123456789"),
                               None)
    MaskPIIFilter().filter(record)
    assert record.getMessage() == "user a***@pes.edu phone ******6789"


def test_no_card_fields_in_complaint_or_any_model():
    """TC-Sec-06 style schema check: no card/CVV/PAN fields anywhere in HMS."""
    from django.apps import apps
    banned = ("card", "cvv", "pan_", "expiry")
    names = [f"{m.__name__}.{f.name}" for m in apps.get_models() for f in m._meta.get_fields()
             if m._meta.app_label in {"accounts", "allocation", "fees", "complaints", "reports", "audit"}]
    assert not [n for n in names if any(b in n.lower() for b in banned)]
    assert Complaint  # complaints app is part of the scan


@pytest.mark.parametrize("logger_name", ["django", "django.server"])
def test_django_loggers_mask_pii(logger_name):
    """Django's own loggers use only the masking handler and do not bypass it via their defaults."""
    logger = logging.getLogger(logger_name)
    handlers = [h for h in logger.handlers if not type(h).__module__.startswith("_pytest")]  # ignore capture
    assert handlers and not logger.propagate
    assert all(any(isinstance(f, MaskPIIFilter) for f in h.filters) for h in handlers)


def test_root_handlers_mask_pii(settings):
    """App loggers (e.g. complaints.services) propagate to root, whose handlers all mask PII."""
    root = settings.LOGGING["root"]["handlers"]
    assert root and all("mask_pii" in settings.LOGGING["handlers"][h]["filters"] for h in root)


def test_student_cannot_reach_admin_records_by_id(client, owner):
    """TC-Sec-01: guessing another record's id from a student account is refused (403)."""
    other = User.objects.create_user("other", email="o@pes.edu", password="Str0ng!pass")
    client.force_login(owner)
    for name, pk in [("allocation:student_edit", other.pk), ("fees:structure_edit", 1)]:
        assert client.get(reverse(name, args=[pk])).status_code == 403
