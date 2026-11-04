"""Restore audit rows from an archive made by `archive_audit` (HMS-NF-004, TC-Ops-01).

    python manage.py restore_audit audit-archive-20261028.jsonl.gz

Only rows whose id is not already in the table are inserted, with their original timestamps,
so restoring the same archive twice changes nothing.
"""
import gzip
import json

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.dateparse import parse_datetime

from audit.models import AuditLog


class Command(BaseCommand):
    help = "Restore audit log rows from a gzip-compressed JSON Lines archive."

    def add_arguments(self, parser):
        parser.add_argument("archive", help="file produced by archive_audit")

    @transaction.atomic
    def handle(self, *args, **opts):
        with gzip.open(opts["archive"], "rt", encoding="utf-8") as fh:
            rows = [json.loads(line) for line in fh if line.strip()]
        existing = set(AuditLog.objects.filter(pk__in=[r["id"] for r in rows]).values_list("pk", flat=True))
        new = [
            AuditLog(**{**r, "timestamp": parse_datetime(r["timestamp"])})
            for r in rows if r["id"] not in existing
        ]
        AuditLog.objects.bulk_create(new)  # insert-only; never updates existing rows
        self.stdout.write(self.style.SUCCESS(
            f"Restored {len(new)} audit rows ({len(rows) - len(new)} already present) from {opts['archive']}"))
