from unittest.mock import patch
from django.contrib.auth.hashers import check_password
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from accounts.models import PasswordResetOTP

User = get_user_model()


@pytest.mark.django_db
@patch("accounts.password_reset_views.send_mail")
def test_forgot_password_creates_hashed_otp(send_mail, client):
    user = User.objects.create_user(
        username="otp-user",
        email="otp@example.com",
        password="OldPass123!",
    )

    with patch("accounts.password_reset_views.secrets.randbelow", return_value=123456):
        response = client.post(
            reverse("accounts:forgot_password"),
            {"email": user.email},
        )

    assert response.status_code == 200
    assert b"If that email is registered" in response.content

    otp_record = PasswordResetOTP.objects.get(user=user)
    assert otp_record.otp_hash != "123456"
    assert check_password("123456", otp_record.otp_hash)
    assert otp_record.expires_at > timezone.now()
    send_mail.assert_called_once()


@pytest.mark.django_db
def test_unknown_email_returns_generic_response(client):
    response = client.post(
        reverse("accounts:forgot_password"),
        {"email": "unknown@example.com"},
    )

    assert response.status_code == 200
    assert b"If that email is registered" in response.content
    assert PasswordResetOTP.objects.count() == 0


@pytest.mark.django_db
@patch("accounts.password_reset_views.send_mail")
def test_reset_password_success_and_single_use(send_mail, client):
    user = User.objects.create_user(
        username="otp-user2",
        email="otp2@example.com",
        password="OldPass123!",
    )

    with patch("accounts.password_reset_views.secrets.randbelow", return_value=123456):
        client.post(
            reverse("accounts:forgot_password"),
            {"email": user.email},
        )

    response = client.post(
        reverse("accounts:reset_password"),
        {
            "email": user.email,
            "otp": "123456",
            "new_password": "NewPass123!xyz",
            "confirm_password": "NewPass123!xyz",
        },
    )

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.check_password("NewPass123!xyz")

    otp_record = PasswordResetOTP.objects.get(user=user)
    assert otp_record.used_at is not None

    second_response = client.post(
        reverse("accounts:reset_password"),
        {
            "email": user.email,
            "otp": "123456",
            "new_password": "AnotherPass123!xyz",
            "confirm_password": "AnotherPass123!xyz",
        },
    )

    assert b"Invalid or expired OTP" in second_response.content


@pytest.mark.django_db
@patch("accounts.password_reset_views.send_mail")
def test_expired_otp_is_rejected(send_mail, client):
    user = User.objects.create_user(
        username="otp-user3",
        email="otp3@example.com",
        password="OldPass123!",
    )

    with patch("accounts.password_reset_views.secrets.randbelow", return_value=654321):
        client.post(
            reverse("accounts:forgot_password"),
            {"email": user.email},
        )

    otp_record = PasswordResetOTP.objects.get(user=user)
    otp_record.expires_at = timezone.now()
    otp_record.save(update_fields=["expires_at"])

    response = client.post(
        reverse("accounts:reset_password"),
        {
            "email": user.email,
            "otp": "654321",
            "new_password": "NewPass123!xyz",
            "confirm_password": "NewPass123!xyz",
        },
    )

    assert b"Invalid or expired OTP" in response.content
    user.refresh_from_db()
    assert user.check_password("OldPass123!")
