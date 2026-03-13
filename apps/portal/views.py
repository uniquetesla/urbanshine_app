from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import FormView

from apps.accounts.models import UserRole
from apps.customers.models import Customer
from apps.invoices.models import Invoice
from apps.offers.models import Offer
from apps.orders.models import Order

from .forms import AppointmentRequestForm


def _customer_for_user(user):
    if not user.email:
        return None
    return Customer.objects.filter(email__iexact=user.email).first()


class CustomerPortalView(LoginRequiredMixin, FormView):
    template_name = "portal/dashboard.html"
    form_class = AppointmentRequestForm
    success_url = "/portal/"

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != UserRole.STAMMKUNDE:
            messages.info(request, "Das Kundenportal ist nur für Stammkunden verfügbar.")
            from django.shortcuts import redirect

            return redirect("accounts:dashboard")
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        initial.update(
            {
                "name": self.request.user.get_full_name() or self.request.user.username,
                "email": self.request.user.email,
            }
        )
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = _customer_for_user(self.request.user)
        context["customer"] = customer

        if customer:
            context["orders"] = Order.objects.filter(kunde=customer).order_by("-auftragsnummer")[:10]
            context["invoices"] = Invoice.objects.filter(kunde=customer).order_by("-rechnungsnummer")[:10]
            context["offers"] = Offer.objects.filter(kunde=customer).order_by("-angebotsnummer")[:10]
        else:
            context["orders"] = []
            context["invoices"] = []
            context["offers"] = []
        return context

    def form_valid(self, form):
        customer = _customer_for_user(self.request.user)
        anfrage = form.save(commit=False)
        anfrage.kunde = customer
        anfrage.save()
        messages.success(self.request, "Ihre Terminanfrage wurde erfolgreich gesendet.")
        return super().form_valid(form)
