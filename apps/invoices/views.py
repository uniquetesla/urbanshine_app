from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.urls import reverse_lazy
from django.views.generic import DeleteView, DetailView, ListView

from apps.accounts.models import UserRole
from apps.customers.models import Customer
from apps.core.security import PasswordProtectedDeleteMixin

from .forms import MarkInvoicePaidForm
from .models import Invoice, PaymentStatus
from .services import mark_invoice_as_paid


def _customer_for_user(user):
    if not user.email:
        return None
    return Customer.objects.filter(email__iexact=user.email).first()


class EmployeeOnlyMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role != UserRole.STAMMKUNDE


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
        context["payment_status_paid"] = PaymentStatus.BEZAHLT
        return context


class InvoiceDetailView(LoginRequiredMixin, DetailView):
    model = Invoice
    template_name = "invoices/invoice_detail.html"
    context_object_name = "invoice"

    def get_queryset(self):
        queryset = super().get_queryset().select_related("kunde", "auftrag", "verkauf").prefetch_related("positionen")
        if self.request.user.role == UserRole.STAMMKUNDE:
            customer = _customer_for_user(self.request.user)
            if not customer:
                return queryset.none()
            return queryset.filter(kunde=customer)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["payment_status_paid"] = PaymentStatus.BEZAHLT
        return context


class InvoiceMarkPaidView(EmployeeOnlyMixin, LoginRequiredMixin, View):
    def post(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk)
        form = MarkInvoicePaidForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Rechnung konnte nicht als bezahlt markiert werden.")
            next_url = request.POST.get("next")
            if next_url:
                return redirect(next_url)
            return redirect("invoices:invoice_detail", pk=pk)

        changed = mark_invoice_as_paid(invoice, paid_date=form.cleaned_data.get("bezahlt_am"))
        if changed:
            messages.success(request, f"Rechnung {invoice.formatted_rechnungsnummer} wurde als bezahlt markiert.")
        else:
            messages.info(request, f"Rechnung {invoice.formatted_rechnungsnummer} ist bereits bezahlt.")
        next_url = request.POST.get("next")
        if next_url:
            return redirect(next_url)
        return redirect("invoices:invoice_detail", pk=pk)


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


class InvoiceDeleteView(PasswordProtectedDeleteMixin, LoginRequiredMixin, DeleteView):
    model = Invoice
    template_name = "invoices/invoice_confirm_delete.html"
    success_url = reverse_lazy("invoices:invoice_list")
    success_message = "Rechnung wurde gelöscht."

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, self.success_message)
        return response
