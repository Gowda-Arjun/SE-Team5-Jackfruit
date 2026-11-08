import uuid
from pathlib import Path

from django.conf import settings
from django.db import models


def complaint_photo_path(instance, filename):
    """Random stored file name so uploads can't overwrite or guess each other (TC-Sec-09)."""
    return f"complaints/{uuid.uuid4().hex}{Path(filename).suffix.lower()}"


class Complaint(models.Model):
    """Maintenance complaint raised by a student (HMS-F-030). Status workflow is HMS-F-031."""

    class Category(models.TextChoices):
        ELECTRICAL = "ELECTRICAL", "Electrical"
        PLUMBING = "PLUMBING", "Plumbing"
        FURNITURE = "FURNITURE", "Furniture"
        CLEANING = "CLEANING", "Cleaning"
        INTERNET = "INTERNET", "Internet / Wi-Fi"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        RESOLVED = "RESOLVED", "Resolved"

    ticket_id = models.CharField(max_length=20, unique=True, editable=False)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="complaints")
    category = models.CharField(max_length=12, choices=Category.choices)
    description = models.TextField(max_length=2000)
    photo = models.FileField(upload_to=complaint_photo_path, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN, db_index=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name="assigned_complaints")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.ticket_id} ({self.get_status_display()})"


# Allowed status moves (HMS-F-031): Open -> In Progress -> Resolved only.
ALLOWED_TRANSITIONS = {
    Complaint.Status.OPEN: {Complaint.Status.IN_PROGRESS},
    Complaint.Status.IN_PROGRESS: {Complaint.Status.RESOLVED},
    Complaint.Status.RESOLVED: set(),
}


class ComplaintStatusHistory(models.Model):
    """One row per status change, shown to the student as a timeline (AC-F-031)."""

    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name="history")
    old_status = models.CharField(max_length=12, choices=Complaint.Status.choices, blank=True)
    new_status = models.CharField(max_length=12, choices=Complaint.Status.choices)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["changed_at", "pk"]

    def __str__(self):
        return f"{self.complaint.ticket_id}: {self.old_status or '-'} -> {self.new_status}"
