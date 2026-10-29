from django.conf import settings
from django.db import models
from django.utils import timezone


class AuditLog(models.Model):
    """Append-only record of admin actions and fee transactions (HMS-SR-004, SAD ADR-07).

    Rows are only ever inserted through audit.services.write_audit(); updates and
    deletes are refused at the model level and hidden in the Django admin.
    """

    class Outcome(models.TextChoices):
        SUCCESS = "SUCCESS", "Success"
        DENIED = "DENIED", "Denied"
        FAILED = "FAILED", "Failed"

    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                              on_delete=models.PROTECT, related_name="audit_entries")
    action = models.CharField(max_length=64)
    target_type = models.CharField(max_length=64, blank=True)
    target_id = models.CharField(max_length=64, blank=True)
    outcome = models.CharField(max_length=8, choices=Outcome.choices, default=Outcome.SUCCESS)
    timestamp = models.DateTimeField(default=timezone.now, editable=False, db_index=True)
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [models.Index(fields=["target_type", "target_id"])]

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise PermissionError("Audit log entries are immutable.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("Audit log entries cannot be deleted.")

    def __str__(self):
        return f"{self.timestamp:%Y-%m-%d %H:%M} {self.actor} {self.action} {self.target_type}:{self.target_id}"
