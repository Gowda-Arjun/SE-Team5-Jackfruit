import uuid

from django.db import transaction

from .models import Complaint


@transaction.atomic
def raise_complaint(student, category, description, photo=None):
    """Create a complaint with a unique ticket id and status Open (HMS-F-030, AC-F-030)."""
    complaint = Complaint.objects.create(
        ticket_id=f"TMP-{uuid.uuid4().hex[:12]}",  # replaced below once the primary key is known
        student=student,
        category=category,
        description=description,
        photo=photo or "",
    )
    complaint.ticket_id = f"CMP-{complaint.pk:06d}"
    complaint.save(update_fields=["ticket_id"])
    return complaint
