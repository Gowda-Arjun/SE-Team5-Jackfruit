from django.urls import path

from . import views

app_name = "fees"

urlpatterns = [
    path("my/", views.my_fees, name="my_fees"),
    path("structures/", views.structure_list, name="structure_list"),
    path("structures/new/", views.structure_create, name="structure_create"),
    path("structures/<int:pk>/edit/", views.structure_edit, name="structure_edit"),
]
