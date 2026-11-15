from django.contrib import admin
from django.db import transaction

from audit.services import write_audit
from .models import FeeStatement, FeeStructure, Payment, Receipt


@admin.register(FeeStatement)
class FeeStatementAdmin(admin.ModelAdmin):
    list_display = ("student", "term", "amount_due", "amount_paid", "due_date")
    list_filter = ("term",)
    search_fields = ("student__username", "student__email", "term")


@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ("term", "room_type", "amount", "due_date", "effective_from")
    list_filter = ("term", "room_type")
    search_fields = ("term",)

    def save_model(self, request, obj, form, change):
        with transaction.atomic():
            super().save_model(request, obj, form, change)
            write_audit(request.user, "FEE_STRUCTURE_SAVED", obj)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "statement",
        "amount",
        "status",
        "gateway_order_id",
        "gateway_txn_id",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = (
        "gateway_order_id",
        "gateway_txn_id",
        "statement__student__username",
        "statement__student__email",
    )
    readonly_fields = (
        "statement",
        "amount",
        "status",
        "gateway_order_id",
        "gateway_txn_id",
        "created_at",
        "updated_at",
    )


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ("receipt_no", "payment", "created_at")
    search_fields = (
        "receipt_no",
        "payment__gateway_txn_id",
        "payment__statement__student__username",
        "payment__statement__student__roll_number",
    )
    readonly_fields = ("payment", "receipt_no", "created_at")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
