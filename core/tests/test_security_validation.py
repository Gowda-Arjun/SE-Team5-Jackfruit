"""Security validation cases from STP 5.1 that had no automated test yet (HMS-36)."""
import logging

import pytest
from django.test import Client
from django.urls import reverse

from accounts.models import User


class _Capture(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)


@pytest.mark.django_db
def test_post_without_csrf_token_is_rejected():
    """TC-Sec-08: a form POST without a CSRF token gets 403."""
    User.objects.create_user("csrf1", email="csrf1@pes.edu", password="Str0ng!pass")
    client = Client(enforce_csrf_checks=True)
    resp = client.post(reverse("accounts:login"), {"username": "csrf1", "password": "Str0ng!pass"})
    assert resp.status_code == 403
    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
def test_denied_role_access_returns_403_and_is_logged(client):
    """HMS-F-005 / AC-F-005, TC-Sec-04: a Student on a Warden/Admin page gets 403 and the attempt is logged."""
    student = User.objects.create_user("rbac1", email="rbac1@pes.edu", password="Str0ng!pass")
    client.force_login(student)
    handler = _Capture()
    logger = logging.getLogger("django.request")
    logger.addHandler(handler)
    try:
        resp = client.get(reverse("reports:index"))
    finally:
        logger.removeHandler(handler)
    assert resp.status_code == 403
    assert any(r.levelno == logging.WARNING and "Forbidden" in r.getMessage() for r in handler.records)
