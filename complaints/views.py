from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import User
from core.decorators import role_required

from .forms import ComplaintForm
from .models import ALLOWED_TRANSITIONS, Complaint
from .services import InvalidTransition, change_complaint_status, raise_complaint

STAFF_ROLES = (User.Role.ADMIN, User.Role.WARDEN, User.Role.TECHNICIAN)


@role_required(User.Role.STUDENT)
def complaint_create(request):
    form = ComplaintForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        complaint = raise_complaint(request.user, **form.cleaned_data)
        messages.success(request, f"Complaint {complaint.ticket_id} raised. Status: Open.")
        return redirect("complaints:my_complaints")
    return render(request, "complaints/complaint_form.html", {"form": form})


@role_required(User.Role.STUDENT)
def my_complaints(request):
    complaints = request.user.complaints.all()  # only the logged-in student's own tickets
    return render(request, "complaints/my_complaints.html", {"complaints": complaints})


@role_required(User.Role.STUDENT)
def complaint_detail(request, ticket_id):
    """Student's own ticket with its status timeline. Another student's ticket is a 404 (no IDOR)."""
    complaint = get_object_or_404(Complaint, ticket_id=ticket_id, student=request.user)
    return render(request, "complaints/complaint_detail.html",
                  {"complaint": complaint, "history": complaint.history.select_related("changed_by")})


def staff_queryset(user):
    """Admin/Warden see every complaint; a Technician sees only complaints assigned to them."""
    qs = Complaint.objects.select_related("student", "assigned_to")
    return qs.filter(assigned_to=user) if user.role == User.Role.TECHNICIAN else qs


@role_required(*STAFF_ROLES)
def complaint_queue(request):
    status = request.GET.get("status", "")
    qs = staff_queryset(request.user)
    if status in Complaint.Status.values:
        qs = qs.filter(status=status)
    page = Paginator(qs, 25).get_page(request.GET.get("page"))
    for c in page:
        c.next_statuses = [(s, Complaint.Status(s).label) for s in ALLOWED_TRANSITIONS[c.status]]
    return render(request, "complaints/complaint_queue.html",
                  {"page": page, "status": status, "statuses": Complaint.Status.choices})


@require_POST
@role_required(*STAFF_ROLES)
def complaint_update_status(request, ticket_id):
    complaint = get_object_or_404(staff_queryset(request.user), ticket_id=ticket_id)
    try:
        change_complaint_status(complaint, request.POST.get("status", ""), request.user)
        messages.success(request, f"{ticket_id} updated. The student has been notified.")
    except InvalidTransition:
        messages.error(request, "This status change is not allowed.")
    return redirect("complaints:queue")
