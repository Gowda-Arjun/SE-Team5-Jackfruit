import pytest
from django.db import transaction

from accounts.models import User
from audit.models import AuditLog
from audit.services import write_audit


@pytest.fixture
def admin_user(db):
    return User.objects.create_user("warden", email="w@pes.edu", password="Str0ng!pass", role=User.Role.ADMIN)


def test_write_audit_records_actor_action_target(admin_user):
    entry = write_audit(admin_user, "STUDENT_DEACTIVATED", admin_user, details={"reason": "left hostel"})
    assert entry.actor == admin_user
    assert entry.target_type == "User" and entry.target_id == str(admin_user.pk)
    assert entry.outcome == AuditLog.Outcome.SUCCESS
    assert entry.details == {"reason": "left hostel"} and entry.timestamp is not None


def test_audit_entry_cannot_be_updated(admin_user):
    """TC-Sec-05: audit log is immutable."""
    entry = write_audit(admin_user, "FEE_STRUCTURE_EDITED")
    entry.action = "TAMPERED"
    with pytest.raises(PermissionError):
        entry.save()
    assert AuditLog.objects.get(pk=entry.pk).action == "FEE_STRUCTURE_EDITED"


def test_audit_entry_cannot_be_deleted(admin_user):
    entry = write_audit(admin_user, "ROOM_ALLOCATED")
    with pytest.raises(PermissionError):
        entry.delete()
    assert AuditLog.objects.count() == 1


@pytest.mark.django_db(transaction=True)
def test_audit_rolls_back_with_callers_transaction():
    actor = User.objects.create_user("a2", email="a2@pes.edu", password="Str0ng!pass", role=User.Role.ADMIN)
    with pytest.raises(RuntimeError):
        with transaction.atomic():
            write_audit(actor, "ROOM_ALLOCATED")
            raise RuntimeError("allocation failed")
    assert AuditLog.objects.count() == 0


def test_anonymous_actor_stored_as_null(db):
    from django.contrib.auth.models import AnonymousUser
    entry = write_audit(AnonymousUser(), "LOGIN_FAILED", outcome=AuditLog.Outcome.DENIED)
    assert entry.actor is None and entry.outcome == "DENIED"


def test_admin_screen_is_read_only(client, admin_user):
    admin_user.is_staff = admin_user.is_superuser = True
    admin_user.save()
    client.force_login(admin_user)
    entry = write_audit(admin_user, "ROOM_ALLOCATED")
    assert client.get("/admin/audit/auditlog/").status_code == 200
    assert client.get("/admin/audit/auditlog/add/").status_code == 403
    assert client.post(f"/admin/audit/auditlog/{entry.pk}/delete/", {"post": "yes"}).status_code == 403


@pytest.mark.django_db(transaction=True)
def test_database_blocks_bulk_update_on_postgres():
    """The model guard can be bypassed by queryset.update(); the PostgreSQL trigger cannot."""
    from django.db import connection
    if connection.vendor != "postgresql":
        pytest.skip("trigger is PostgreSQL-only (runs in CI)")
    from django.db import DatabaseError
    write_audit(None, "ROOM_ALLOCATED")
    with pytest.raises(DatabaseError):
        AuditLog.objects.update(action="TAMPERED")
