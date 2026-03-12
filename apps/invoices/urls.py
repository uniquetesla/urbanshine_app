from django.urls import path

from .views import InvoiceDetailView, InvoiceListView

app_name = "invoices"

urlpatterns = [
    path("", InvoiceListView.as_view(), name="invoice_list"),
    path("<int:pk>/", InvoiceDetailView.as_view(), name="invoice_detail"),
]
