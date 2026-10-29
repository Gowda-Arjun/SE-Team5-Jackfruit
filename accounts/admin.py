from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import StudentProfile, User


@admin.register(User)
class HMSUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("HMS", {"fields": ("role", "roll_number")}),)
    list_display = ("username", "email", "roll_number", "role", "is_active")
    list_filter = ("role", "is_active")


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("full_name", "user", "gender", "phone")
    search_fields = ("full_name", "user__roll_number", "user__email")
