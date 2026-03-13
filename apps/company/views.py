from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView, UpdateView, View

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


MASTER_DATA_CONFIG = {
    "service": {"model": Service, "form": ServiceForm, "success": "Leistung gespeichert."},
    "price": {"model": Price, "form": PriceForm, "success": "Preis gespeichert."},
    "order_type": {"model": OrderType, "form": OrderTypeForm, "success": "Auftragsart gespeichert."},
    "soiling_level": {"model": SoilingLevel, "form": SoilingLevelForm, "success": "Verschmutzungsgrad gespeichert."},
    "surcharge": {"model": Surcharge, "form": SurchargeForm, "success": "Zuschlag gespeichert."},
}


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

        if action in MASTER_DATA_CONFIG:
            form_class = MASTER_DATA_CONFIG[action]["form"]
            success_message = MASTER_DATA_CONFIG[action]["success"]
            form = form_class(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, success_message)
            else:
                messages.error(request, "Bitte Eingaben prüfen.")

        return redirect("company:master_data")


class MasterDataDeleteView(MasterDataAccessMixin, View):
    def post(self, request, model_name, pk):
        config = MASTER_DATA_CONFIG.get(model_name)
        model = config["model"] if config else None
        if not model:
            messages.error(request, "Ungültiger Datensatztyp.")
            return redirect(reverse_lazy("company:master_data"))

        instance = get_object_or_404(model, pk=pk)
        instance.delete()
        messages.success(request, "Eintrag wurde gelöscht.")
        return redirect(reverse_lazy("company:master_data"))


class MasterDataUpdateView(MasterDataAccessMixin, UpdateView):
    template_name = "company/master_data_edit.html"

    def dispatch(self, request, *args, **kwargs):
        self.model_name = kwargs["model_name"]
        self.config = MASTER_DATA_CONFIG.get(self.model_name)
        if not self.config:
            messages.error(request, "Ungültiger Datensatztyp.")
            return redirect("company:master_data")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.config["model"].objects.all()

    def get_form_class(self):
        return self.config["form"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_name"] = self.model_name
        context["model_title"] = self.config["model"]._meta.verbose_name
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        label = self.config["model"]._meta.verbose_name.title()
        messages.success(self.request, f"{label} wurde aktualisiert.")
        return response

    def get_success_url(self):
        return reverse_lazy("company:master_data")
