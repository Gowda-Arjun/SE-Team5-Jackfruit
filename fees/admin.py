from django.contrib import admin
from django.db import transaction

from audit.services import write_audit
from .models import FeeStructure


@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ("term", "room_type", "amount", "due_date", "effective_from")
    list_filter = ("term", "room_type")
    search_fields = ("term",)

    def save_model(self, request, obj, form, change):
        with transaction.atomic():
            super().save_model(request, obj, form, change)
            write_audit(request.user, "FEE_STRUCTURE_SAVED", obj)
