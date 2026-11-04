from django.contrib import admin

from .models import Block, Room


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ("name", "gender_policy")
    search_fields = ("name",)


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("block", "number", "floor", "room_type", "capacity", "occupancy", "is_active")
    list_filter = ("block", "room_type", "is_active", "floor")
    search_fields = ("number", "block__name")
