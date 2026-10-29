from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Read-only view of the audit trail: no add, change or delete (HMS-SR-004)."""

    list_display = ("timestamp", "actor", "action", "target_type", "target_id", "outcome")
    list_filter = ("action", "outcome")
    search_fields = ("action", "target_type", "target_id", "actor__username")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
