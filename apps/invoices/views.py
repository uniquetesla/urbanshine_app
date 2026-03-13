from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import DetailView, ListView

from apps.accounts.models import UserRole
from apps.customers.models import Customer

from .models import Invoice


def _customer_for_user(user):
    if not user.email:
        return None
    return Customer.objects.filter(email__iexact=user.email).first()


class InvoiceListView(LoginRequiredMixin, ListView):
    model = Invoice
    template_name = "invoices/invoice_list.html"
    context_object_name = "invoices"

    def get_queryset(self):
        queryset = Invoice.objects.select_related("kunde", "auftrag", "verkauf")

        if self.request.user.role == UserRole.STAMMKUNDE:
            customer = _customer_for_user(self.request.user)
            if not customer:
                return queryset.none()
            queryset = queryset.filter(kunde=customer)

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

    def get_queryset(self):
        queryset = super().get_queryset().select_related("kunde", "auftrag", "verkauf")
        if self.request.user.role == UserRole.STAMMKUNDE:
            customer = _customer_for_user(self.request.user)
            if not customer:
                return queryset.none()
            return queryset.filter(kunde=customer)
        return queryset


class InvoiceDownloadPdfView(LoginRequiredMixin, View):
    def get(self, request, pk):
        queryset = Invoice.objects.all()
        if request.user.role == UserRole.STAMMKUNDE:
            customer = _customer_for_user(request.user)
            if not customer:
                raise Http404
            queryset = queryset.filter(kunde=customer)

        invoice = get_object_or_404(queryset, pk=pk)
        if not invoice.pdf_datei:
            raise Http404("Für diese Rechnung ist keine PDF-Datei vorhanden.")
        return FileResponse(invoice.pdf_datei.open("rb"), as_attachment=True, filename=invoice.pdf_datei.name.split("/")[-1])
