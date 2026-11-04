from django.urls import path

from . import views

app_name = "allocation"

urlpatterns = [
    path("rooms/", views.room_list, name="room_list"),
    path("rooms/create/", views.room_create, name="room_create"),
    path("rooms/<int:pk>/edit/", views.room_edit, name="room_edit"),
    path("rooms/<int:pk>/deactivate/", views.room_deactivate, name="room_deactivate"),
    path("blocks/", views.block_list, name="block_list"),
    path("blocks/create/", views.block_create, name="block_create"),
    path("blocks/<int:pk>/edit/", views.block_edit, name="block_edit"),
]
