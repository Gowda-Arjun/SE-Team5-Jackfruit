from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from .forms import StudentProfileForm
from .models import StudentProfile


@login_required
def profile(request):
    if not request.user.is_student:
        raise PermissionDenied

    student_profile = get_object_or_404(
        StudentProfile,
        user=request.user
    )

    if request.method == "POST":
        form = StudentProfileForm(
            request.POST,
            instance=student_profile
        )

        if form.is_valid():
            form.save()
            messages.success(request, "Your profile was updated successfully.")
            return redirect("accounts:profile")
    else:
        form = StudentProfileForm(instance=student_profile)

    return render(
        request,
        "accounts/profile.html",
        {
            "form": form,
            "student_profile": student_profile,
        },
    )
