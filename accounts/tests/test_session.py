
import time
import pytest

from django.test import override_settings
from django.urls import reverse
from accounts.models import User


@pytest.fixture
def student(db):
    return User.objects.create_user(
        username="session_student",
        email="session_student@pes.edu",
        password="test-password",
        role=User.Role.STUDENT,
    )


@pytest.mark.django_db
@override_settings(SESSION_COOKIE_AGE=1200)
def test_session_expiry_age_is_20_minutes(client, student):
    client.force_login(student)
    assert client.session.get_expiry_age() == 1200


@pytest.mark.django_db
@override_settings(
    SESSION_COOKIE_AGE=10,
    SESSION_SAVE_EVERY_REQUEST=True,
)
def test_active_request_refreshes_session_expiry(client, student):
    client.force_login(student)

    client.get(reverse("core:home"))
    original_expiry = client.session.get_expiry_date()

    time.sleep(1.1)

    client.get(reverse("core:home"))
    refreshed_expiry = client.session.get_expiry_date()

    assert refreshed_expiry > original_expiry


@pytest.mark.django_db
@override_settings(SESSION_COOKIE_AGE=1)
def test_expired_session_redirects_to_login(client, student):
    client.force_login(student)
    time.sleep(2)

    response = client.get(reverse("core:home"))

    assert response.status_code == 302
    assert response.url.startswith(reverse("accounts:login"))
