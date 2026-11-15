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
    path("students/", views.student_list, name="student_list"),
    path("students/create/", views.student_create, name="student_create"),
    path("students/<int:pk>/edit/", views.student_edit, name="student_edit"),
    path("students/<int:pk>/deactivate/", views.student_deactivate, name="student_deactivate"),
    path("allocate/", views.allocate, name="allocate"),
    path("my-room/", views.my_room, name="my_room"),
    path("room-change/", views.room_change_request, name="room_change_request"),
    path("room-change-queue/", views.room_change_queue, name="room_change_queue"),
]
