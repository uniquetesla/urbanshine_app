from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import DetailView, ListView

from apps.orders.models import Order, OrderStatus

from .forms import OfferForm, OfferItemFormSet
from .models import Offer, OfferStatus


class OfferListView(LoginRequiredMixin, ListView):
    model = Offer
    template_name = "offers/offer_list.html"
    context_object_name = "offers"

    def get_queryset(self):
        return Offer.objects.select_related("kunde", "umgewandelter_auftrag")


class OfferCreateView(LoginRequiredMixin, View):
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
            messages.success(request, "Angebot wurde erstellt.")
            return redirect("offers:offer_detail", pk=offer.pk)
        return self._render(request, form, formset)

    def _render(self, request, form, formset):
        from django.shortcuts import render

        return render(request, self.template_name, {"form": form, "formset": formset})


class OfferDetailView(LoginRequiredMixin, DetailView):
    model = Offer
    template_name = "offers/offer_detail.html"
    context_object_name = "offer"


class OfferConvertToOrderView(LoginRequiredMixin, View):
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
