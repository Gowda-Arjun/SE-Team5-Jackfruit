import pytest
from django.core import mail
from django.urls import reverse

from accounts.models import User
from audit.models import AuditLog
from complaints.models import Complaint
from complaints.services import InvalidTransition, change_complaint_status, raise_complaint

OPEN, IN_PROGRESS, RESOLVED = Complaint.Status.OPEN, Complaint.Status.IN_PROGRESS, Complaint.Status.RESOLVED


@pytest.fixture
def student(db):
    return User.objects.create_user("stu1", email="stu1@pes.edu", password="Str0ng!pass")


@pytest.fixture
def warden(db):
    return User.objects.create_user("war", email="war@pes.edu", password="Str0ng!pass", role=User.Role.WARDEN)


@pytest.fixture
def complaint(student):
    return raise_complaint(student, "PLUMBING", "Leaking tap")


@pytest.mark.django_db(transaction=True)
def test_full_workflow_records_history_audit_and_notifies(student, warden):
    """TC-Maint-02 / AC-F-031: Open -> In Progress -> Resolved, timestamped, student notified."""
    complaint = raise_complaint(student, "PLUMBING", "Leaking tap")
    change_complaint_status(complaint, IN_PROGRESS, warden)
    change_complaint_status(complaint, RESOLVED, warden)
    complaint.refresh_from_db()
    assert complaint.status == RESOLVED
    assert [h.new_status for h in complaint.history.all()] == [OPEN, IN_PROGRESS, RESOLVED]
    assert all(h.changed_at for h in complaint.history.all())
    assert AuditLog.objects.filter(action="COMPLAINT_STATUS_CHANGE", outcome="SUCCESS").count() == 2
    assert len(mail.outbox) == 2 and mail.outbox[-1].to == ["stu1@pes.edu"]
    assert "Resolved" in mail.outbox[-1].subject


@pytest.mark.parametrize("start,target", [
    (OPEN, RESOLVED),          # cannot skip In Progress
    (IN_PROGRESS, OPEN),       # cannot go backwards
])
def test_invalid_transitions_rejected_and_audited(complaint, warden, start, target):
    Complaint.objects.filter(pk=complaint.pk).update(status=start)
    with pytest.raises(InvalidTransition):
        change_complaint_status(complaint, target, warden)
    complaint.refresh_from_db()
    assert complaint.status == start


def test_resolved_back_to_open_is_refused(complaint, warden):
    change_complaint_status(complaint, IN_PROGRESS, warden)
    change_complaint_status(complaint, RESOLVED, warden)
    with pytest.raises(InvalidTransition):
        change_complaint_status(complaint, OPEN, warden)


def test_garbage_status_rejected(complaint, warden):
    with pytest.raises(InvalidTransition):
        change_complaint_status(complaint, "DELETED", warden)


def test_warden_updates_status_from_queue(client, complaint, warden):
    client.force_login(warden)
    assert complaint.ticket_id in client.get(reverse("complaints:queue")).content.decode()
    client.post(reverse("complaints:update_status", args=[complaint.ticket_id]), {"status": IN_PROGRESS})
    complaint.refresh_from_db()
    assert complaint.status == IN_PROGRESS


def test_queue_filter_by_status(client, student, warden):
    a = raise_complaint(student, "OTHER", "first")
    b = raise_complaint(student, "OTHER", "second")
    change_complaint_status(b, IN_PROGRESS, warden)
    client.force_login(warden)
    page = client.get(reverse("complaints:queue"), {"status": IN_PROGRESS}).content.decode()
    assert b.ticket_id in page and a.ticket_id not in page


def test_student_cannot_open_queue_or_change_status(client, student, complaint):
    client.force_login(student)
    assert client.get(reverse("complaints:queue")).status_code == 403
    url = reverse("complaints:update_status", args=[complaint.ticket_id])
    assert client.post(url, {"status": IN_PROGRESS}).status_code == 403


def test_technician_sees_only_assigned(client, student):
    tech = User.objects.create_user("tech", email="t@pes.edu", password="Str0ng!pass", role=User.Role.TECHNICIAN)
    mine = raise_complaint(student, "ELECTRICAL", "Fan")
    other = raise_complaint(student, "ELECTRICAL", "Light")
    Complaint.objects.filter(pk=mine.pk).update(assigned_to=tech)
    client.force_login(tech)
    page = client.get(reverse("complaints:queue")).content.decode()
    assert mine.ticket_id in page and other.ticket_id not in page
    resp = client.post(reverse("complaints:update_status", args=[other.ticket_id]), {"status": IN_PROGRESS})
    assert resp.status_code == 404


def test_student_sees_timeline_on_own_ticket(client, student, complaint, warden):
    change_complaint_status(complaint, IN_PROGRESS, warden)
    client.force_login(student)
    page = client.get(reverse("complaints:detail", args=[complaint.ticket_id])).content.decode()
    assert "Open" in page and "In Progress" in page


def test_student_cannot_view_another_students_ticket(client, complaint):
    """IDOR protection: another student's ticket id returns 404."""
    other = User.objects.create_user("stu2", email="stu2@pes.edu", password="Str0ng!pass")
    client.force_login(other)
    assert client.get(reverse("complaints:detail", args=[complaint.ticket_id])).status_code == 404
