import logging
import uuid

from django.core.mail import send_mail
from django.db import transaction

from audit.services import write_audit

from .models import ALLOWED_TRANSITIONS, Complaint, ComplaintStatusHistory

logger = logging.getLogger(__name__)


class InvalidTransition(Exception):
    """Raised for a status change outside Open -> In Progress -> Resolved (error code INVALID_TRANSITION)."""


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
    ComplaintStatusHistory.objects.create(complaint=complaint, new_status=Complaint.Status.OPEN, changed_by=student)
    return complaint


def change_complaint_status(complaint, new_status, actor):
    """Move a complaint to its next status (HMS-F-031, SAD 4.3 internal interface).

    Allows only Open -> In Progress -> Resolved, records a history row and an audit entry in
    one transaction, then notifies the student after commit (a failed email never rolls back).
    """
    with transaction.atomic():
        complaint = Complaint.objects.select_for_update().get(pk=complaint.pk)
        old_status = complaint.status
        if new_status not in ALLOWED_TRANSITIONS.get(old_status, set()):
            write_audit(actor, "COMPLAINT_STATUS_CHANGE", complaint, outcome="DENIED",
                        details={"from": old_status, "to": new_status})
            raise InvalidTransition(f"Cannot move {complaint.ticket_id} from {old_status} to {new_status}.")
        complaint.status = new_status
        complaint.save(update_fields=["status", "updated_at"])
        ComplaintStatusHistory.objects.create(complaint=complaint, old_status=old_status,
                                              new_status=new_status, changed_by=actor)
        write_audit(actor, "COMPLAINT_STATUS_CHANGE", complaint, details={"from": old_status, "to": new_status})
        transaction.on_commit(lambda: notify_student(complaint))
    return complaint


def notify_student(complaint):
    """Email the student about a status change. Failures are logged, never raised (SAD 4.3 Notifier)."""
    try:
        send_mail(
            subject=f"[HMS] Complaint {complaint.ticket_id} is now {complaint.get_status_display()}",
            message=(f"Your {complaint.get_category_display().lower()} complaint {complaint.ticket_id} "
                     f"has been updated to: {complaint.get_status_display()}."),
            from_email=None,
            recipient_list=[complaint.student.email],
        )
    except Exception:  # noqa: BLE001 - notification must never break the request
        logger.exception("Complaint notification failed for %s", complaint.ticket_id)
