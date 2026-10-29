from django.urls import path

from . import views

app_name = "complaints"

urlpatterns = [
    path("", views.my_complaints, name="my_complaints"),
    path("new/", views.complaint_create, name="create"),
]
