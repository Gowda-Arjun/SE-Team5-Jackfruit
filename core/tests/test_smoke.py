import pytest
from django.urls import reverse

from accounts.models import User


@pytest.mark.django_db
def test_health_check(client):
    assert client.get(reverse("core:healthz")).json() == {"status": "ok"}


@pytest.mark.django_db
def test_home_requires_login(client):
    resp = client.get(reverse("core:home"))
    assert resp.status_code == 302
    assert reverse("accounts:login") in resp.url


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,heading",
    [(User.Role.STUDENT, "Welcome"), (User.Role.ADMIN, "Warden / Admin dashboard")],
)
def test_dashboard_by_role(client, role, heading):
    user = User.objects.create_user("u1", email="u1@pes.edu", password="Str0ng!pass", role=role)
    client.force_login(user)
    assert heading in client.get(reverse("core:home")).content.decode()


@pytest.mark.django_db
def test_password_is_hashed():
    """HMS-SR-002: passwords are stored as salted hashes, never plaintext."""
    user = User.objects.create_user("u2", email="u2@pes.edu", password="Str0ng!pass")
    assert user.password.startswith(("pbkdf2_sha256$", "argon2"))
    assert "Str0ng!pass" not in user.password


@pytest.mark.django_db
def test_login_page_and_login_flow(client):
    assert client.get(reverse("accounts:login")).status_code == 200
    User.objects.create_user("stu", email="stu@pes.edu", password="Str0ng!pass")
    resp = client.post(reverse("accounts:login"), {"username": "stu", "password": "Str0ng!pass"})
    assert resp.status_code == 302 and resp.url == reverse("core:home")
