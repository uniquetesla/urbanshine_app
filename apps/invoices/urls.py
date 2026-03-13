from django.urls import path

from .views import InvoiceDetailView, InvoiceDownloadPdfView, InvoiceListView, InvoiceMarkPaidView

app_name = "invoices"

urlpatterns = [
    path("", InvoiceListView.as_view(), name="invoice_list"),
    path("<int:pk>/", InvoiceDetailView.as_view(), name="invoice_detail"),
    path("<int:pk>/als-bezahlt-markieren/", InvoiceMarkPaidView.as_view(), name="invoice_mark_paid"),
    path("<int:pk>/pdf/", InvoiceDownloadPdfView.as_view(), name="invoice_pdf"),
]
