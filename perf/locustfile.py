"""Locust workload for the authenticated student pages (HMS-NF-001)."""

import re

from locust import HttpUser, between, task


class StudentUser(HttpUser):
    """Load the dashboard, room and complaints pages as student01."""

    wait_time = between(0.5, 1.5)

    def on_start(self):
        response = self.client.get("/accounts/login/")
        csrf_match = re.search(
            rb'name="csrfmiddlewaretoken" value="([^"]+)"',
            response.content,
        )
        if csrf_match is None:
            raise RuntimeError("Login page did not contain a CSRF token.")

        login_response = self.client.post(
            "/accounts/login/",
            {
                "username": "student01",
                "password": "Hostel@Demo2026",
                "csrfmiddlewaretoken": csrf_match.group(1).decode(),
            },
            headers={"Referer": f"{self.host}/accounts/login/"},
        )
        if login_response.status_code not in (200, 302):
            raise RuntimeError(
                f"student01 login failed with HTTP {login_response.status_code}"
            )

    @task(3)
    def dashboard(self):
        self.client.get("/", name="dashboard")

    @task(2)
    def my_room(self):
        self.client.get("/allocation/my-room/", name="my room")

    @task(2)
    def complaints(self):
        self.client.get("/complaints/", name="complaints")
