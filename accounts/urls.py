from django.contrib.auth import views as auth_views
from django.urls import path

app_name = "accounts"

urlpatterns = [
    # Basic login/logout from the setup PR. HMS-F-001 adds registration and
    # roll-number login; HMS-F-002/003 add profile and OTP reset here.
    path("login/", auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
