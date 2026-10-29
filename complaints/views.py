from django.contrib import messages
from django.shortcuts import redirect, render

from accounts.models import User
from core.decorators import role_required

from .forms import ComplaintForm
from .services import raise_complaint


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
