import datetime
import gzip
import json

import pytest
from django.core.management import call_command
from django.db import connection
from django.utils import timezone

from accounts.models import User
from audit.models import AuditLog
from audit.services import write_audit


@pytest.fixture
def actor(db):
    return User.objects.create_user("aud", email="aud@pes.edu", password="Str0ng!pass", role=User.Role.ADMIN)


def make_old_entry(actor, days_ago):
    return AuditLog.objects.create(actor=actor, action="OLD_ACTION",
                                   timestamp=timezone.now() - datetime.timedelta(days=days_ago))


def read_archive(path):
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh]


def test_retention_setting_is_three_years(settings):
    """HMS-NF-004: audit logs are retained for at least 3 years."""
    assert settings.AUDIT_RETENTION_DAYS >= 3 * 365


def test_archive_exports_only_rows_past_retention(actor, tmp_path):
    make_old_entry(actor, days_ago=4 * 365)
    write_audit(actor, "RECENT_ACTION")
    out = tmp_path / "a.jsonl.gz"
    call_command("archive_audit", out=str(out))
    rows = read_archive(out)
    assert [r["action"] for r in rows] == ["OLD_ACTION"]
    assert AuditLog.objects.count() == 2  # archiving never deletes from the append-only table


def test_archive_all(actor, tmp_path):
    write_audit(actor, "A")
    write_audit(actor, "B")
    out = tmp_path / "all.jsonl.gz"
    call_command("archive_audit", "--all", out=str(out))
    assert {r["action"] for r in read_archive(out)} == {"A", "B"}


@pytest.mark.django_db(transaction=True)
def test_restore_round_trip_keeps_original_timestamps(tmp_path):
    """TC-Ops-01: archived logs are retrievable on request."""
    actor = User.objects.create_user("aud2", email="aud2@pes.edu", password="Str0ng!pass")
    old = make_old_entry(actor, days_ago=1200)
    original_ts = old.timestamp
    out = tmp_path / "rt.jsonl.gz"
    call_command("archive_audit", "--all", out=str(out))
    # simulate the rows having been moved off the live database
    with connection.cursor() as cur:
        if connection.vendor == "postgresql":
            cur.execute("ALTER TABLE audit_auditlog DISABLE TRIGGER audit_log_no_update_delete")
        cur.execute("DELETE FROM audit_auditlog")
        if connection.vendor == "postgresql":
            cur.execute("ALTER TABLE audit_auditlog ENABLE TRIGGER audit_log_no_update_delete")
    assert AuditLog.objects.count() == 0
    call_command("restore_audit", str(out))
    restored = AuditLog.objects.get(pk=old.pk)
    assert restored.action == "OLD_ACTION" and restored.timestamp == original_ts and restored.actor_id == actor.pk


def test_restore_twice_does_not_duplicate(actor, tmp_path):
    write_audit(actor, "ONCE")
    out = tmp_path / "dup.jsonl.gz"
    call_command("archive_audit", "--all", out=str(out))
    call_command("restore_audit", str(out))
    call_command("restore_audit", str(out))
    assert AuditLog.objects.filter(action="ONCE").count() == 1
