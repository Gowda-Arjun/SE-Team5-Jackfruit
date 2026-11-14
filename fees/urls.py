from django.urls import path

from . import views

app_name = "fees"

urlpatterns = [
    path("my/", views.my_fees, name="my_fees"),
    path("payments/<int:statement_id>/pay/", views.pay, name="pay"),
    path(
        "payments/<int:payment_id>/mock-checkout/",
        views.mock_checkout,
        name="mock_checkout",
    ),
    path(
        "payments/<int:payment_id>/razorpay-checkout/",
        views.razorpay_checkout,
        name="razorpay_checkout",
    ),
    path("webhook/", views.webhook, name="webhook"),
    path("structures/", views.structure_list, name="structure_list"),
    path("structures/new/", views.structure_create, name="structure_create"),
    path("structures/<int:pk>/edit/", views.structure_edit, name="structure_edit"),
]
