"""Export audit log rows to a compressed archive file (HMS-NF-004, SAD 4.4).

    python manage.py archive_audit                      # rows older than AUDIT_RETENTION_DAYS (3 years)
    python manage.py archive_audit --all                # every row (for the demo / backups)
    python manage.py archive_audit --out audit.jsonl.gz

Rows stay in the database: the audit table is append-only (HMS-SR-004), so the archive is an
offline copy that can be restored on request with `python manage.py restore_audit <file>`.
"""
import datetime
import gzip
import json

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from audit.models import AuditLog

FIELDS = ("id", "actor_id", "action", "target_type", "target_id", "outcome", "timestamp", "details")


class Command(BaseCommand):
    help = "Export audit log rows to a gzip-compressed JSON Lines archive."

    def add_arguments(self, parser):
        parser.add_argument("--all", action="store_true", help="archive every row, not only expired ones")
        parser.add_argument("--days", type=int, default=getattr(settings, "AUDIT_RETENTION_DAYS", 3 * 365),
                            help="archive rows older than this many days (default: retention period)")
        parser.add_argument("--out", help="output file (default: audit-archive-<date>.jsonl.gz)")

    def handle(self, *args, **opts):
        qs = AuditLog.objects.order_by("timestamp", "pk")
        if not opts["all"]:
            qs = qs.filter(timestamp__lt=timezone.now() - datetime.timedelta(days=opts["days"]))
        out = opts["out"] or f"audit-archive-{timezone.now():%Y%m%d-%H%M%S}.jsonl.gz"
        count = 0
        with gzip.open(out, "wt", encoding="utf-8") as fh:
            for row in qs.values(*FIELDS).iterator():
                row["timestamp"] = row["timestamp"].isoformat()
                fh.write(json.dumps(row, separators=(",", ":")) + "\n")
                count += 1
        self.stdout.write(self.style.SUCCESS(f"Archived {count} audit rows to {out}"))
