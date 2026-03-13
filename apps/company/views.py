from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView, View

from apps.accounts.models import UserRole
from apps.core.models import NumberSequence, NumberSequenceType
from apps.core.number_sequences import ensure_sequence

from .forms import (
    CompanySettingsForm,
    NumberSequenceFormSet,
    OrderTypeForm,
    PriceForm,
    ServiceForm,
    SoilingLevelForm,
    SurchargeForm,
)
from .models import CompanySettings, OrderType, Price, Service, SoilingLevel, Surcharge


class MasterDataAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.role in {UserRole.ADMIN, UserRole.CHEF}


class MasterDataView(MasterDataAccessMixin, TemplateView):
    template_name = "company/master_data.html"

    def _sequence_formset(self, data=None):
        for sequence_type, _label in NumberSequenceType.choices:
            ensure_sequence(sequence_type)
        return NumberSequenceFormSet(data, queryset=NumberSequence.objects.order_by("sequence_type"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        settings_instance, _ = CompanySettings.objects.get_or_create(company_name="UrbanShine")

        context.update(
            {
                "service_form": ServiceForm(),
                "price_form": PriceForm(),
                "order_type_form": OrderTypeForm(),
                "soiling_level_form": SoilingLevelForm(),
                "surcharge_form": SurchargeForm(),
                "company_form": CompanySettingsForm(instance=settings_instance),
                "number_sequence_formset": kwargs.get("number_sequence_formset") or self._sequence_formset(),
                "services": Service.objects.all(),
                "prices": Price.objects.all(),
                "order_types": OrderType.objects.all(),
                "soiling_levels": SoilingLevel.objects.all(),
                "surcharges": Surcharge.objects.all(),
                "company_settings": settings_instance,
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        form_map = {
            "service": (ServiceForm, "Leistung gespeichert."),
            "price": (PriceForm, "Preis gespeichert."),
            "order_type": (OrderTypeForm, "Auftragsart gespeichert."),
            "soiling_level": (SoilingLevelForm, "Verschmutzungsgrad gespeichert."),
            "surcharge": (SurchargeForm, "Zuschlag gespeichert."),
        }

        if action == "number_sequences":
            formset = self._sequence_formset(request.POST)
            if formset.is_valid():
                formset.save()
                messages.success(request, "Nummernkreise wurden gespeichert.")
                return redirect("company:master_data")
            messages.error(request, "Nummernkreise konnten nicht gespeichert werden.")
            return self.render_to_response(self.get_context_data(number_sequence_formset=formset))

        if action == "company_settings":
            settings_instance, _ = CompanySettings.objects.get_or_create(company_name="UrbanShine")
            form = CompanySettingsForm(request.POST, request.FILES, instance=settings_instance)
            if form.is_valid():
                form.save()
                messages.success(request, "Firmendaten wurden gespeichert.")
            else:
                messages.error(request, "Firmendaten konnten nicht gespeichert werden.")
            return redirect("company:master_data")

        if action in form_map:
            form_class, success_message = form_map[action]
            form = form_class(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, success_message)
            else:
                messages.error(request, "Bitte Eingaben prüfen.")

        return redirect("company:master_data")


class MasterDataDeleteView(MasterDataAccessMixin, View):
    model_map = {
        "service": Service,
        "price": Price,
        "order_type": OrderType,
        "soiling_level": SoilingLevel,
        "surcharge": Surcharge,
    }

    def post(self, request, model_name, pk):
        model = self.model_map.get(model_name)
        if not model:
            messages.error(request, "Ungültiger Datensatztyp.")
            return redirect(reverse_lazy("company:master_data"))

        instance = get_object_or_404(model, pk=pk)
        instance.delete()
        messages.success(request, "Eintrag wurde gelöscht.")
        return redirect(reverse_lazy("company:master_data"))
