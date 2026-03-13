from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.accounts.models import UserRole
from apps.core.activity import log_activity
from apps.core.models import ActivitySubject
from apps.customers.models import Customer
from apps.invoices.services import create_invoice_for_completed_order, create_manual_invoice_for_order
from apps.company.models import Service, SoilingLevel, Surcharge

from .forms import OrderForm, OrderPositionFormSet
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
        queryset = Order.objects.select_related("kunde", "order_type").prefetch_related("mitarbeiter", "rechnungen").order_by("-auftragsnummer")

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
                | Q(positionen__leistung__name__icontains=query)
                | Q(status__icontains=query)
            ).distinct()
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

    def get_success_url(self):
        return reverse_lazy("orders:order_detail", kwargs={"pk": self.object.pk})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["files"] = self.request.FILES or None
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["position_formset"] = kwargs.get("position_formset") or OrderPositionFormSet(self.request.POST or None)
        context.update(_get_price_context())
        return context

    def form_invalid(self, form):
        messages.error(self.request, "Auftrag konnte nicht gespeichert werden. Bitte die markierten Felder prüfen.")
        return super().form_invalid(form)

    def form_valid(self, form):
        position_formset = OrderPositionFormSet(self.request.POST, self.request.FILES)
        if not position_formset.is_valid():
            return self.render_to_response(self.get_context_data(form=form, position_formset=position_formset))

        with transaction.atomic():
            response = super().form_valid(form)
            position_formset.instance = self.object
            position_formset.save()
            self.object.recalculate_totals(save=True)
            self._save_files()

        log_activity(
            actor=self.request.user,
            subject_type=ActivitySubject.AUFTRAG,
            subject_label=f"Auftrag #{self.object.auftragsnummer}",
            action="Auftrag erstellt",
            details=self.object.auftragsart,
            to_state=self.object.get_status_display(),
            icon="🧽",
        )
        messages.success(self.request, "Auftrag wurde erfolgreich angelegt.")
        return response

    def _save_files(self):
        for file_obj in self.request.FILES.getlist("bilder"):
            OrderImage.objects.create(auftrag=self.object, bild=file_obj)


class OrderUpdateView(EmployeeOnlyMixin, LoginRequiredMixin, UpdateView):
    model = Order
    form_class = OrderForm
    template_name = "orders/order_form.html"

    def get_success_url(self):
        return reverse_lazy("orders:order_detail", kwargs={"pk": self.object.pk})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["files"] = self.request.FILES or None
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["position_formset"] = kwargs.get("position_formset") or OrderPositionFormSet(
            self.request.POST or None, instance=self.object
        )
        context.update(_get_price_context())
        return context

    def form_invalid(self, form):
        messages.error(self.request, "Auftrag konnte nicht gespeichert werden. Bitte die markierten Felder prüfen.")
        return super().form_invalid(form)

    def form_valid(self, form):
        old_status = self.get_object().status
        position_formset = OrderPositionFormSet(self.request.POST, self.request.FILES, instance=self.object)
        if not position_formset.is_valid():
            return self.render_to_response(self.get_context_data(form=form, position_formset=position_formset))

        with transaction.atomic():
            response = super().form_valid(form)
            position_formset.save()
            self.object.recalculate_totals(save=True)
            self._save_files()

        if old_status != self.object.status and self.object.status == OrderStatus.ABGESCHLOSSEN:
            invoice_exists = self.object.rechnungen.exists()
            invoice = create_invoice_for_completed_order(self.object)
            if invoice and not invoice_exists:
                messages.success(self.request, f"Rechnung R-{invoice.rechnungsnummer:05d} wurde erstellt.")

        log_activity(
            actor=self.request.user,
            subject_type=ActivitySubject.AUFTRAG,
            subject_label=f"Auftrag #{self.object.auftragsnummer}",
            action="Auftrag bearbeitet",
            details=self.object.auftragsart,
            from_state=dict(OrderStatus.choices).get(old_status, old_status),
            to_state=self.object.get_status_display(),
            icon="🔧",
        )
        messages.success(self.request, "Auftrag wurde erfolgreich bearbeitet.")
        return response

    def _save_files(self):
        for file_obj in self.request.FILES.getlist("bilder"):
            OrderImage.objects.create(auftrag=self.object, bild=file_obj)


class OrderDeleteView(EmployeeOnlyMixin, LoginRequiredMixin, DeleteView):
    model = Order
    template_name = "orders/order_confirm_delete.html"
    success_url = reverse_lazy("orders:order_list")


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = "orders/order_detail.html"
    context_object_name = "order"

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .select_related("kunde", "order_type")
            .prefetch_related("mitarbeiter", "bilder", "rechnungen", "positionen__leistung", "positionen__verschmutzungsgrad", "positionen__zuschlag")
        )
        if self.request.user.role == UserRole.STAMMKUNDE:
            customer = _customer_for_user(self.request.user)
            if not customer:
                return queryset.none()
            return queryset.filter(kunde=customer)
        return queryset


class OrderCreateInvoiceView(EmployeeOnlyMixin, LoginRequiredMixin, View):
    def post(self, request, pk):
        order = get_object_or_404(Order.objects.select_related("kunde"), pk=pk)
        existing_invoice = order.rechnungen.first()
        if existing_invoice:
            messages.info(request, f"Für Auftrag {order.auftragsnummer} existiert bereits eine Rechnung.")
            return redirect(request.POST.get("next") or "orders:order_list")

        invoice = create_manual_invoice_for_order(order)
        messages.success(request, f"Rechnung R-{invoice.rechnungsnummer:05d} wurde erstellt.")
        return redirect(request.POST.get("next") or "orders:order_list")


class OrderQuickStatusUpdateView(EmployeeOnlyMixin, LoginRequiredMixin, View):
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        new_status = request.POST.get("status")
        if new_status not in dict(OrderStatus.choices):
            messages.error(request, "Ungültiger Status.")
            return redirect(request.POST.get("next") or "orders:order_list")

        order.status = new_status
        order.save(update_fields=["status", "updated_at"])
        messages.success(request, f"Status für Auftrag {order.auftragsnummer} aktualisiert.")
        return redirect(request.POST.get("next") or "orders:order_list")


def _get_price_context():
    return {
        "service_prices": {str(service.pk): str(service.price) for service in Service.objects.all()},
        "service_durations": {str(service.pk): service.estimated_duration_minutes for service in Service.objects.all()},
        "soiling_multipliers": {
            str(level.pk): str(level.multiplier) for level in SoilingLevel.objects.all()
        },
        "surcharge_values": {
            str(surcharge.pk): {
                "amount": str(surcharge.amount),
                "is_percentage": surcharge.is_percentage,
            }
            for surcharge in Surcharge.objects.all()
        },
    }
