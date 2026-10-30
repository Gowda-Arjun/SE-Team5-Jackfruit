import pytest
from django.core.management import call_command

from accounts.models import StudentProfile, User


@pytest.mark.django_db
def test_seed_demo_creates_users_and_is_idempotent():
    call_command("seed_demo")
    call_command("seed_demo")  # running twice must not duplicate anything
    assert User.objects.filter(role=User.Role.STUDENT).count() == 10
    assert User.objects.get(username="admin").role == User.Role.ADMIN
    assert User.objects.get(username="warden").role == User.Role.WARDEN
    assert StudentProfile.objects.filter(gender="M").count() == 5
    assert StudentProfile.objects.filter(gender="F").count() == 5


@pytest.mark.django_db
def test_seeded_accounts_can_log_in(client):
    from core.management.commands.seed_demo import DEMO_PASSWORD
    call_command("seed_demo")
    assert client.login(username="student01", password=DEMO_PASSWORD)
