from django.urls import path

from . import views

app_name = "complaints"

urlpatterns = [
    path("", views.my_complaints, name="my_complaints"),
    path("new/", views.complaint_create, name="create"),
    path("queue/", views.complaint_queue, name="queue"),
    path("<str:ticket_id>/", views.complaint_detail, name="detail"),
    path("<str:ticket_id>/status/", views.complaint_update_status, name="update_status"),
    path("<str:ticket_id>/photo/", views.complaint_photo, name="photo"),
]
