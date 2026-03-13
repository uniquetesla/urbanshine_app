from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, ListView

from apps.accounts.models import UserRole
from apps.core.activity import log_activity
from apps.core.models import ActivitySubject
from apps.customers.models import Customer
from apps.orders.models import Order, OrderStatus

from .forms import OfferForm, OfferItemFormSet
from .models import Offer, OfferStatus


def _customer_for_user(user):
    if not user.email:
        return None
    return Customer.objects.filter(email__iexact=user.email).first()


class EmployeeOnlyMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role != UserRole.STAMMKUNDE


class OfferListView(LoginRequiredMixin, ListView):
    model = Offer
    template_name = "offers/offer_list.html"
    context_object_name = "offers"

    def get_queryset(self):
        queryset = Offer.objects.select_related("kunde", "umgewandelter_auftrag")
        if self.request.user.role == UserRole.STAMMKUNDE:
            customer = _customer_for_user(self.request.user)
            if not customer:
                return queryset.none()
            queryset = queryset.filter(kunde=customer)
        return queryset


class OfferCreateView(EmployeeOnlyMixin, LoginRequiredMixin, View):
    template_name = "offers/offer_form.html"

    def get(self, request):
        form = OfferForm()
        formset = OfferItemFormSet(prefix="positionen")
        return self._render(request, form, formset)

    def post(self, request):
        form = OfferForm(request.POST)
        formset = OfferItemFormSet(request.POST, prefix="positionen")
        if form.is_valid() and formset.is_valid():
            offer = form.save()
            formset.instance = offer
            formset.save()
            log_activity(
                actor=request.user,
                subject_type=ActivitySubject.ANGEBOT,
                subject_label=f"Angebot A-{offer.angebotsnummer:05d}",
                action="Angebot erstellt",
                details=offer.titel,
                icon="💼",
            )
            messages.success(request, "Angebot wurde erstellt.")
            return redirect("offers:offer_detail", pk=offer.pk)
        return self._render(request, form, formset)

    def _render(self, request, form, formset):
        return render(request, self.template_name, {"form": form, "formset": formset})


class OfferDetailView(LoginRequiredMixin, DetailView):
    model = Offer
    template_name = "offers/offer_detail.html"
    context_object_name = "offer"

    def get_queryset(self):
        queryset = super().get_queryset().select_related("kunde", "umgewandelter_auftrag").prefetch_related("positionen")
        if self.request.user.role == UserRole.STAMMKUNDE:
            customer = _customer_for_user(self.request.user)
            if not customer:
                return queryset.none()
            queryset = queryset.filter(kunde=customer)
        return queryset


class OfferConvertToOrderView(EmployeeOnlyMixin, LoginRequiredMixin, View):
    def post(self, request, pk):
        offer = get_object_or_404(Offer.objects.prefetch_related("positionen"), pk=pk)

        if offer.umgewandelter_auftrag:
            messages.info(request, "Angebot wurde bereits in einen Auftrag umgewandelt.")
            return redirect("offers:offer_detail", pk=offer.pk)

        leistungen = "\n".join(
            f"- {item.bezeichnung}: {item.menge} × {item.einzelpreis} € = {item.gesamtpreis} €"
            for item in offer.positionen.all()
        )
        if not leistungen:
            messages.error(request, "Angebot ohne Positionen kann nicht umgewandelt werden.")
            return redirect("offers:offer_detail", pk=offer.pk)

        order = Order.objects.create(
            kunde=offer.kunde,
            auftragsart=offer.titel,
            leistungen=leistungen,
            preisberechnung=(
                f"Zwischensumme: {offer.zwischensumme} €\n"
                f"Rabatt: {offer.rabatt_prozent}% ({offer.rabatt_betrag} €)\n"
                f"Gesamt: {offer.gesamtpreis} €"
            ),
            gesamtpreis=offer.gesamtpreis,
            zuschlaege=0,
            status=OrderStatus.NEU,
            interne_notizen=f"Automatisch aus Angebot A-{offer.angebotsnummer:05d} erstellt.",
        )

        offer.umgewandelter_auftrag = order
        offer.status = OfferStatus.UMGEWANDELT
        offer.save(update_fields=["umgewandelter_auftrag", "status", "updated_at"])

        messages.success(request, f"Angebot wurde in Auftrag #{order.auftragsnummer} umgewandelt.")
        return redirect(reverse("orders:order_detail", kwargs={"pk": order.pk}))
