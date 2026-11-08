from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .password_reset_views import forgot_password, reset_password

app_name = "accounts"

urlpatterns = [
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="accounts/login.html"),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),
    path(
        "profile/",
        views.profile,
        name="profile",
    ),
    path("forgot-password/", forgot_password, name="forgot_password"),
    path("reset-password/", reset_password, name="reset_password"),
]
