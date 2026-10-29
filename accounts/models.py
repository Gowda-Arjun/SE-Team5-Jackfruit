from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """HMS user. Role drives role-based access control (HMS-F-001, HMS-F-005)."""

    class Role(models.TextChoices):
        STUDENT = "STUDENT", "Student"
        WARDEN = "WARDEN", "Warden"
        ADMIN = "ADMIN", "Admin"
        TECHNICIAN = "TECHNICIAN", "Technician"

    email = models.EmailField(unique=True)
    roll_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    role = models.CharField(max_length=12, choices=Role.choices, default=Role.STUDENT)

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT

    @property
    def is_staff_role(self):
        """Warden or Admin - can use the admin/warden console."""
        return self.role in (self.Role.WARDEN, self.Role.ADMIN)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class StudentProfile(models.Model):
    """Student personal details (SAD 3.6). Shared by AuthModule (HMS-F-002) and
    AllocationModule (HMS-F-011 records, HMS-F-012 gender policy)."""

    class Gender(models.TextChoices):
        MALE = "M", "Male"
        FEMALE = "F", "Female"
        OTHER = "O", "Other"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    full_name = models.CharField(max_length=120)
    gender = models.CharField(max_length=1, choices=Gender.choices)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    guardian_name = models.CharField(max_length=120, blank=True)
    guardian_phone = models.CharField(max_length=15, blank=True)
    emergency_contact = models.CharField(max_length=120, blank=True)

    def __str__(self):
        return f"{self.full_name} ({self.user.roll_number or self.user.username})"
