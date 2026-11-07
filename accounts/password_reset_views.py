
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import send_mail
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .models import PasswordResetOTP
from .password_reset_forms import RequestResetForm, VerifyResetOTPForm

User = get_user_model()


@require_http_methods(["GET", "POST"])
def forgot_password(request):
    form = RequestResetForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"].strip().lower()
        user = User.objects.filter(email__iexact=email).first()

        # Generic response prevents email enumeration.
        if user:
            otp = f"{secrets.randbelow(1_000_000):06d}"

            PasswordResetOTP.objects.create(
                user=user,
                otp_hash=make_password(otp),
                expires_at=timezone.now() + timedelta(minutes=10),
            )

            send_mail(
                subject="Your password reset OTP",
                message=f"Your password reset OTP is {otp}. It expires in 10 minutes.",
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                recipient_list=[user.email],
                fail_silently=False,
            )

        return render(
            request,
            "accounts/forgot_password.html",
            {
                "form": RequestResetForm(),
                "message": (
                    "If that email is registered, "
                    "a reset OTP has been sent."
                ),
            },
        )

    return render(
        request,
        "accounts/forgot_password.html",
        {"form": form},
    )


@require_http_methods(["GET", "POST"])
def reset_password(request):
    form = VerifyResetOTPForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"].strip().lower()
        otp = form.cleaned_data["otp"]

        user = User.objects.filter(email__iexact=email).first()
        record = None

        if user:
            record = PasswordResetOTP.objects.filter(
                user=user,
                used_at__isnull=True,
                expires_at__gt=timezone.now(),
            ).order_by("-created_at").first()

        valid = bool(record and check_password(otp, record.otp_hash))

        if valid:
            user.set_password(form.cleaned_data["new_password"])
            user.save(update_fields=["password"])

            record.used_at = timezone.now()
            record.save(update_fields=["used_at"])

            # Invalidate all remaining OTPs for this user.
            PasswordResetOTP.objects.filter(
                user=user,
                used_at__isnull=True,
            ).exclude(pk=record.pk).update(
                used_at=timezone.now()
            )

            return render(
                request,
                "accounts/reset_password.html",
                {
                    "form": VerifyResetOTPForm(),
                    "success": (
                        "Password reset successfully. "
                        "You can now sign in."
                    ),
                },
            )

        form.add_error(
            None,
            "Invalid or expired OTP. Request a new one and try again.",
        )

    return render(
        request,
        "accounts/reset_password.html",
        {"form": form},
    )
