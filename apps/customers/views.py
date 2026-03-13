from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.accounts.models import UserRole

from .forms import CustomerForm
from .models import Customer


class EmployeeOnlyMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role != UserRole.STAMMKUNDE


class CustomerListView(LoginRequiredMixin, ListView):
    model = Customer
    template_name = "customers/customer_list.html"
    context_object_name = "customers"

    def get_queryset(self):
        queryset = Customer.objects.order_by("kundennummer")
        if self.request.user.role == UserRole.STAMMKUNDE:
            if not self.request.user.email:
                return queryset.none()
            queryset = queryset.filter(email__iexact=self.request.user.email)

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


class CustomerCreateView(EmployeeOnlyMixin, LoginRequiredMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = "customers/customer_form.html"
    success_url = reverse_lazy("customers:customer_list")

    def form_valid(self, form):
        messages.success(self.request, "Kunde wurde erfolgreich angelegt.")
        return super().form_valid(form)


class CustomerUpdateView(EmployeeOnlyMixin, LoginRequiredMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = "customers/customer_form.html"
    success_url = reverse_lazy("customers:customer_list")

    def form_valid(self, form):
        messages.success(self.request, "Kunde wurde erfolgreich bearbeitet.")
        return super().form_valid(form)


class CustomerDeleteView(EmployeeOnlyMixin, LoginRequiredMixin, DeleteView):
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

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.role == UserRole.STAMMKUNDE:
            if not self.request.user.email:
                return queryset.none()
            return queryset.filter(email__iexact=self.request.user.email)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["auftraege"] = self.object.auftraege.order_by("-created_at")[:5]
        context["rechnungen"] = self.object.rechnungen.order_by("-rechnungsdatum", "-rechnungsnummer")[:5]
        context["angebote"] = self.object.angebote.order_by("-angebotsnummer")[:5]
        context["verkaeufe"] = []
        return context
