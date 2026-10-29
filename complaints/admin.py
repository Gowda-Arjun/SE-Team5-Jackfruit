from django.contrib import admin

from .models import Complaint


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ("ticket_id", "student", "category", "status", "created_at")
    list_filter = ("status", "category")
    search_fields = ("ticket_id", "student__username", "student__roll_number")
    readonly_fields = ("ticket_id", "created_at", "updated_at")
