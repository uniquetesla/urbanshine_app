from django import forms

from .models import CompanySettings, OrderType, Price, Service, SoilingLevel, Surcharge


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ["name", "price", "estimated_duration_minutes", "description", "is_active"]


class PriceForm(forms.ModelForm):
    class Meta:
        model = Price
        fields = ["name", "amount", "unit", "is_active"]


class OrderTypeForm(forms.ModelForm):
    class Meta:
        model = OrderType
        fields = ["name", "is_active"]


class SoilingLevelForm(forms.ModelForm):
    class Meta:
        model = SoilingLevel
        fields = ["name", "multiplier", "is_active"]


class SurchargeForm(forms.ModelForm):
    class Meta:
        model = Surcharge
        fields = ["name", "amount", "is_percentage", "is_active"]


class CompanySettingsForm(forms.ModelForm):
    class Meta:
        model = CompanySettings
        fields = ["company_name", "address", "phone", "email", "logo", "invoice_generation_enabled"]
