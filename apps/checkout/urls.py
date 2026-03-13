from django.urls import path

from .views import CheckoutView, SaleCreateInvoiceView

app_name = "checkout"

urlpatterns = [
    path("", CheckoutView.as_view(), name="pos"),
    path("verkaeufe/<int:pk>/rechnung-erstellen/", SaleCreateInvoiceView.as_view(), name="sale_create_invoice"),
]
