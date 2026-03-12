from django.http import FileResponse, Http404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import DetailView, ListView

from .models import Invoice


class InvoiceListView(LoginRequiredMixin, ListView):
    model = Invoice
    template_name = "invoices/invoice_list.html"
    context_object_name = "invoices"

    def get_queryset(self):
        queryset = Invoice.objects.select_related("kunde", "auftrag")
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(rechnungsnummer__icontains=query)
                | Q(kunde__kundennummer__icontains=query)
                | Q(kunde__vorname__icontains=query)
                | Q(kunde__nachname__icontains=query)
                | Q(zahlungsstatus__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "").strip()
        return context


class InvoiceDetailView(LoginRequiredMixin, DetailView):
    model = Invoice
    template_name = "invoices/invoice_detail.html"
    context_object_name = "invoice"


class InvoiceDownloadPdfView(LoginRequiredMixin, View):
    def get(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk)
        if not invoice.pdf_datei:
            raise Http404("Für diese Rechnung ist keine PDF-Datei vorhanden.")
        return FileResponse(invoice.pdf_datei.open("rb"), as_attachment=True, filename=invoice.pdf_datei.name.split("/")[-1])
