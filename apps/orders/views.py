from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import OrderForm
from .models import Order, OrderImage


class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = "orders/order_list.html"
    context_object_name = "orders"

    def get_queryset(self):
        queryset = Order.objects.select_related("kunde").prefetch_related("mitarbeiter").order_by("-auftragsnummer")
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
        return context


class OrderCreateView(LoginRequiredMixin, CreateView):
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


class OrderUpdateView(LoginRequiredMixin, UpdateView):
    model = Order
    form_class = OrderForm
    template_name = "orders/order_form.html"
    success_url = reverse_lazy("orders:order_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        self._save_images(form)
        messages.success(self.request, "Auftrag wurde erfolgreich bearbeitet.")
        return response

    def _save_images(self, form):
        for image in form.cleaned_data.get("bilder", []):
            OrderImage.objects.create(auftrag=self.object, bild=image)


class OrderDeleteView(LoginRequiredMixin, DeleteView):
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
