from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.accounts.models import UserRole
from apps.customers.models import Customer
from apps.invoices.services import create_invoice_for_completed_order

from .forms import OrderForm
from .models import Order, OrderImage, OrderStatus


def _customer_for_user(user):
    if not user.email:
        return None
    return Customer.objects.filter(email__iexact=user.email).first()


class EmployeeOnlyMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role != UserRole.STAMMKUNDE


class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = "orders/order_list.html"
    context_object_name = "orders"

    def get_queryset(self):
        queryset = Order.objects.select_related("kunde").prefetch_related("mitarbeiter").order_by("-auftragsnummer")

        if self.request.user.role == UserRole.STAMMKUNDE:
            customer = _customer_for_user(self.request.user)
            if not customer:
                return queryset.none()
            queryset = queryset.filter(kunde=customer)

        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(auftragsnummer__icontains=query)
                | Q(kunde__vorname__icontains=query)
                | Q(kunde__nachname__icontains=query)
                | Q(auftragsart__icontains=query)
                | Q(leistungen__icontains=query)
                | Q(status__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "").strip()
        context["status_choices"] = Order._meta.get_field("status").choices
        return context


class OrderCreateView(EmployeeOnlyMixin, LoginRequiredMixin, CreateView):
    model = Order
    form_class = OrderForm
    template_name = "orders/order_form.html"
    success_url = reverse_lazy("orders:order_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        self._save_images(form)
        messages.success(self.request, "Auftrag wurde erfolgreich angelegt.")
        return response

    def _save_images(self, form):
        for image in form.cleaned_data.get("bilder", []):
            OrderImage.objects.create(auftrag=self.object, bild=image)


class OrderUpdateView(EmployeeOnlyMixin, LoginRequiredMixin, UpdateView):
    model = Order
    form_class = OrderForm
    template_name = "orders/order_form.html"
    success_url = reverse_lazy("orders:order_list")

    def form_valid(self, form):
        old_status = self.get_object().status
        response = super().form_valid(form)
        self._save_images(form)
        if old_status != self.object.status and self.object.status == OrderStatus.ABGESCHLOSSEN:
            invoice = create_invoice_for_completed_order(self.object)
            if invoice:
                messages.success(self.request, f"Rechnung R-{invoice.rechnungsnummer:05d} wurde erstellt.")
        messages.success(self.request, "Auftrag wurde erfolgreich bearbeitet.")
        return response

    def _save_images(self, form):
        for image in form.cleaned_data.get("bilder", []):
            OrderImage.objects.create(auftrag=self.object, bild=image)


class OrderDeleteView(EmployeeOnlyMixin, LoginRequiredMixin, DeleteView):
    model = Order
    template_name = "orders/order_confirm_delete.html"
    success_url = reverse_lazy("orders:order_list")

    def form_valid(self, form):
        messages.success(self.request, "Auftrag wurde erfolgreich gelöscht.")
        return super().form_valid(form)


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = "orders/order_detail.html"
    context_object_name = "order"

    def get_queryset(self):
        queryset = super().get_queryset().select_related("kunde").prefetch_related("mitarbeiter", "bilder")
        if self.request.user.role == UserRole.STAMMKUNDE:
            customer = _customer_for_user(self.request.user)
            if not customer:
                return queryset.none()
            return queryset.filter(kunde=customer)
        return queryset


class OrderQuickStatusUpdateView(EmployeeOnlyMixin, LoginRequiredMixin, View):
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        new_status = request.POST.get("status")
        if new_status not in dict(OrderStatus.choices):
            messages.error(request, "Ungültiger Status.")
            return redirect(request.POST.get("next") or "orders:order_list")

        old_status = order.status
        order.status = new_status
        order.save(update_fields=["status", "updated_at"])

        if old_status != new_status and new_status == OrderStatus.ABGESCHLOSSEN:
            invoice = create_invoice_for_completed_order(order)
            if invoice:
                messages.success(request, f"Rechnung R-{invoice.rechnungsnummer:05d} wurde erstellt.")
        messages.success(request, f"Status für Auftrag {order.auftragsnummer} aktualisiert.")
        return redirect(request.POST.get("next") or "orders:order_list")
