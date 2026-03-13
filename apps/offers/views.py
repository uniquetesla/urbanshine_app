from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.accounts.models import UserRole
from apps.company.models import Service, SoilingLevel, Surcharge
from apps.core.security import PasswordProtectedDeleteMixin
from apps.core.activity import log_activity
from apps.core.models import ActivitySubject
from apps.customers.models import Customer
from apps.orders.models import Order, OrderPosition, OrderStatus

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

        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(angebotsnummer__icontains=query)
                | Q(kunde__vorname__icontains=query)
                | Q(kunde__nachname__icontains=query)
                | Q(titel__icontains=query)
                | Q(positionen__leistung__name__icontains=query)
                | Q(status__icontains=query)
            ).distinct()
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "").strip()
        context["status_choices"] = Offer._meta.get_field("status").choices
        return context


class OfferCreateView(EmployeeOnlyMixin, LoginRequiredMixin, CreateView):
    model = Offer
    form_class = OfferForm
    template_name = "offers/offer_form.html"

    def get_success_url(self):
        return reverse_lazy("offers:offer_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["position_formset"] = kwargs.get("position_formset") or OfferItemFormSet(self.request.POST or None)
        context.update(_get_price_context())
        return context

    def form_invalid(self, form):
        messages.error(self.request, "Angebot konnte nicht gespeichert werden. Bitte die markierten Felder prüfen.")
        return super().form_invalid(form)

    def form_valid(self, form):
        position_formset = OfferItemFormSet(self.request.POST)
        if not position_formset.is_valid():
            return self.render_to_response(self.get_context_data(form=form, position_formset=position_formset))

        with transaction.atomic():
            response = super().form_valid(form)
            position_formset.instance = self.object
            position_formset.save()

        log_activity(
            actor=self.request.user,
            subject_type=ActivitySubject.ANGEBOT,
            subject_label=self.object.formatted_angebotsnummer,
            action="Angebot erstellt",
            details=self.object.titel,
            icon="💼",
        )
        messages.success(self.request, "Angebot wurde erstellt.")
        return response


class OfferUpdateView(EmployeeOnlyMixin, LoginRequiredMixin, UpdateView):
    model = Offer
    form_class = OfferForm
    template_name = "offers/offer_form.html"

    def get_success_url(self):
        return reverse_lazy("offers:offer_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["position_formset"] = kwargs.get("position_formset") or OfferItemFormSet(self.request.POST or None, instance=self.object)
        context.update(_get_price_context())
        return context

    def form_invalid(self, form):
        messages.error(self.request, "Angebot konnte nicht gespeichert werden. Bitte die markierten Felder prüfen.")
        return super().form_invalid(form)

    def form_valid(self, form):
        position_formset = OfferItemFormSet(self.request.POST, instance=self.object)
        if not position_formset.is_valid():
            return self.render_to_response(self.get_context_data(form=form, position_formset=position_formset))

        with transaction.atomic():
            response = super().form_valid(form)
            position_formset.save()

        log_activity(
            actor=self.request.user,
            subject_type=ActivitySubject.ANGEBOT,
            subject_label=self.object.formatted_angebotsnummer,
            action="Angebot bearbeitet",
            details=self.object.titel,
            icon="🔧",
        )
        messages.success(self.request, "Angebot wurde bearbeitet.")
        return response


class OfferDeleteView(PasswordProtectedDeleteMixin, LoginRequiredMixin, DeleteView):
    model = Offer
    template_name = "offers/offer_confirm_delete.html"
    success_url = reverse_lazy("offers:offer_list")
    success_message = "Angebot wurde gelöscht."

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, self.success_message)
        return response


class OfferDetailView(LoginRequiredMixin, DetailView):
    model = Offer
    template_name = "offers/offer_detail.html"
    context_object_name = "offer"

    def get_queryset(self):
        queryset = super().get_queryset().select_related("kunde", "umgewandelter_auftrag").prefetch_related(
            "positionen__leistung", "positionen__verschmutzungsgrad", "positionen__zuschlag"
        )
        if self.request.user.role == UserRole.STAMMKUNDE:
            customer = _customer_for_user(self.request.user)
            if not customer:
                return queryset.none()
            queryset = queryset.filter(kunde=customer)
        return queryset


class OfferConvertToOrderView(EmployeeOnlyMixin, LoginRequiredMixin, View):
    def post(self, request, pk):
        offer = get_object_or_404(Offer.objects.prefetch_related("positionen__leistung", "positionen__verschmutzungsgrad", "positionen__zuschlag"), pk=pk)

        if offer.umgewandelter_auftrag:
            messages.info(request, "Angebot wurde bereits in einen Auftrag umgewandelt.")
            return redirect("offers:offer_detail", pk=offer.pk)

        offer_items = [item for item in offer.positionen.all() if item.leistung_id and item.verschmutzungsgrad_id]
        if not offer_items:
            messages.error(request, "Angebot ohne gültige Positionen kann nicht umgewandelt werden.")
            return redirect("offers:offer_detail", pk=offer.pk)

        with transaction.atomic():
            order = Order.objects.create(
                kunde=offer.kunde,
                auftragsart=offer.titel,
                status=OrderStatus.NEU,
                interne_notizen=(
                    f"Automatisch aus Angebot {offer.formatted_angebotsnummer} erstellt."
                    + (f" Enthält {offer.rabatt_prozent}% Angebotsrabatt." if offer.rabatt_prozent else "")
                ),
            )

            for item in offer_items:
                OrderPosition.objects.create(
                    auftrag=order,
                    leistung=item.leistung,
                    verschmutzungsgrad=item.verschmutzungsgrad,
                    zuschlag=item.zuschlag,
                )

            order.recalculate_totals(save=True)

            order.preisberechnung = (
                f"Zwischensumme aus Positionen: {order.gesamtpreis:.2f} €\n"
                f"Angebotsrabatt: {offer.rabatt_prozent:.2f}% ({offer.rabatt_betrag:.2f} €)\n"
                f"Angebotsgesamtpreis: {offer.gesamtpreis:.2f} €"
            )
            order.save(update_fields=["preisberechnung", "updated_at"])

            offer.umgewandelter_auftrag = order
            offer.status = OfferStatus.UMGEWANDELT
            offer.save(update_fields=["umgewandelter_auftrag", "status", "updated_at"])

        messages.success(request, f"Angebot wurde in Auftrag {order.formatted_auftragsnummer} umgewandelt.")
        return redirect(reverse("orders:order_detail", kwargs={"pk": order.pk}))


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
