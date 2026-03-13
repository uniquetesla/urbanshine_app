from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from apps.accounts.models import UserRole
from apps.core.models import NumberSequence, NumberSequenceType
from apps.core.number_sequences import ensure_sequence

from .forms import CompanySettingsForm, NumberSequenceForm, OrderTypeForm, PriceForm, ServiceForm, SoilingLevelForm, SurchargeForm
from .models import CompanySettings, OrderType, Price, Service, SoilingLevel, Surcharge


MASTER_DATA_MODULES = {
    "service": {"model": Service, "form": ServiceForm, "title": "Leistungen", "fields": ["name", "price", "unit", "estimated_duration_minutes", "is_active"]},
    "order_type": {"model": OrderType, "form": OrderTypeForm, "title": "Auftragsarten", "fields": ["name", "is_active"]},
    "soiling_level": {"model": SoilingLevel, "form": SoilingLevelForm, "title": "Verschmutzungsgrade", "fields": ["name", "multiplier", "is_active"]},
    "surcharge": {"model": Surcharge, "form": SurchargeForm, "title": "Zuschläge", "fields": ["name", "amount", "is_percentage", "is_active"]},
    "price": {"model": Price, "form": PriceForm, "title": "Artikelpreise", "fields": ["name", "amount", "unit", "is_active"]},
    "number_sequence": {"model": NumberSequence, "form": NumberSequenceForm, "title": "Nummernkreise", "fields": ["sequence_type", "prefix", "separator", "start_value", "padding", "last_value"]},
}


class MasterDataAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.role in {UserRole.ADMIN, UserRole.CHEF}


class MasterDataView(MasterDataAccessMixin, TemplateView):
    template_name = "company/master_data.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for sequence_type, _label in NumberSequenceType.choices:
            ensure_sequence(sequence_type)
        context["modules"] = MASTER_DATA_MODULES
        context["company_settings"] = CompanySettings.objects.first()
        return context


class MasterDataModuleMixin(MasterDataAccessMixin):
    module_name = None

    def dispatch(self, request, *args, **kwargs):
        self.module_name = kwargs.get("module")
        self.module = MASTER_DATA_MODULES.get(self.module_name)
        if not self.module:
            messages.error(request, "Unbekanntes Admin-Modul.")
            return redirect("company:master_data")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.module["model"].objects.all()

    def get_form_class(self):
        return self.module["form"]

    def get_success_url(self):
        return reverse_lazy("company:master_data_module_list", kwargs={"module": self.module_name})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["module"] = self.module
        context["module_name"] = self.module_name
        context["module_title"] = self.module["title"]
        context["list_fields"] = self.module["fields"]
        return context


class MasterDataModuleListView(MasterDataModuleMixin, ListView):
    template_name = "company/module_list.html"
    context_object_name = "items"

    def get_queryset(self):
        queryset = super().get_queryset().order_by("id")
        query = self.request.GET.get("q", "").strip()
        if query and hasattr(self.module["model"], "name"):
            queryset = queryset.filter(name__icontains=query)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "").strip()
        return context


class MasterDataModuleCreateView(MasterDataModuleMixin, CreateView):
    template_name = "company/module_form.html"

    def form_valid(self, form):
        messages.success(self.request, f"{self.module['title']} erfolgreich angelegt.")
        return super().form_valid(form)


class MasterDataModuleDetailView(MasterDataModuleMixin, DetailView):
    template_name = "company/module_detail.html"
    context_object_name = "item"


class MasterDataModuleUpdateView(MasterDataModuleMixin, UpdateView):
    template_name = "company/module_form.html"

    def form_valid(self, form):
        messages.success(self.request, f"{self.module['title']} wurde aktualisiert.")
        return super().form_valid(form)


class MasterDataModuleDeleteView(MasterDataModuleMixin, DeleteView):
    template_name = "company/module_confirm_delete.html"

    def form_valid(self, form):
        messages.success(self.request, "Eintrag wurde gelöscht.")
        return super().form_valid(form)


class CompanySettingsDetailView(MasterDataAccessMixin, DetailView):
    template_name = "company/company_settings_detail.html"
    context_object_name = "settings"

    def get_object(self, queryset=None):
        return CompanySettings.objects.first() or CompanySettings.objects.create(company_name="UrbanShine")


class CompanySettingsUpdateView(MasterDataAccessMixin, UpdateView):
    form_class = CompanySettingsForm
    template_name = "company/company_settings_form.html"
    success_url = reverse_lazy("company:company_settings_detail")

    def get_object(self, queryset=None):
        return CompanySettings.objects.first() or CompanySettings.objects.create(company_name="UrbanShine")

    def form_valid(self, form):
        messages.success(self.request, "Firmendaten wurden erfolgreich gespeichert.")
        return super().form_valid(form)
