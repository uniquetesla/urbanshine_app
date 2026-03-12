from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import CustomerForm
from .models import Customer


class CustomerListView(LoginRequiredMixin, ListView):
    model = Customer
    template_name = "customers/customer_list.html"
    context_object_name = "customers"

    def get_queryset(self):
        queryset = Customer.objects.order_by("kundennummer")
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(kundennummer__icontains=query)
                | Q(vorname__icontains=query)
                | Q(nachname__icontains=query)
                | Q(ort__icontains=query)
                | Q(email__icontains=query)
                | Q(telefon__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "").strip()
        return context


class CustomerCreateView(LoginRequiredMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = "customers/customer_form.html"
    success_url = reverse_lazy("customers:customer_list")

    def form_valid(self, form):
        messages.success(self.request, "Kunde wurde erfolgreich angelegt.")
        return super().form_valid(form)


class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = "customers/customer_form.html"
    success_url = reverse_lazy("customers:customer_list")

    def form_valid(self, form):
        messages.success(self.request, "Kunde wurde erfolgreich bearbeitet.")
        return super().form_valid(form)


class CustomerDeleteView(LoginRequiredMixin, DeleteView):
    model = Customer
    template_name = "customers/customer_confirm_delete.html"
    success_url = reverse_lazy("customers:customer_list")

    def form_valid(self, form):
        messages.success(self.request, "Kunde wurde erfolgreich gelöscht.")
        return super().form_valid(form)


class CustomerDetailView(LoginRequiredMixin, DetailView):
    model = Customer
    template_name = "customers/customer_detail.html"
    context_object_name = "customer"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["auftraege"] = self.object.auftraege.order_by("-created_at")[:5]
        context["rechnungen"] = []
        context["angebote"] = []
        context["verkaeufe"] = []
        return context
