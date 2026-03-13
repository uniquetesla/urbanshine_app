from django.contrib import admin

from .models import CompanySettings, OrderType, Price, Service, SoilingLevel, Surcharge


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "unit", "price", "estimated_duration_minutes", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "description", "unit")
    list_editable = ("unit", "price", "estimated_duration_minutes", "is_active")


@admin.register(Price)
class PriceAdmin(admin.ModelAdmin):
    list_display = ("name", "amount", "unit", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "unit")
    list_editable = ("amount", "unit", "is_active")


@admin.register(OrderType)
class OrderTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
    list_editable = ("is_active",)


@admin.register(SoilingLevel)
class SoilingLevelAdmin(admin.ModelAdmin):
    list_display = ("name", "multiplier", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
    list_editable = ("multiplier", "is_active")


@admin.register(Surcharge)
class SurchargeAdmin(admin.ModelAdmin):
    list_display = ("name", "amount", "is_percentage", "is_active")
    list_filter = ("is_active", "is_percentage")
    search_fields = ("name",)
    list_editable = ("amount", "is_percentage", "is_active")


@admin.register(CompanySettings)
class CompanySettingsAdmin(admin.ModelAdmin):
    list_display = ("company_name", "email", "phone", "invoice_generation_enabled", "updated_at")
    readonly_fields = ("updated_at",)
    fieldsets = (("Unternehmen", {"fields": ("company_name", "address", "tax_id")}), ("Kontakt", {"fields": ("phone", "email", "website")}), ("Finanzen", {"fields": ("bank_name", "iban", "bic", "kleinunternehmerregelung")}), ("Rechnung", {"fields": ("invoice_generation_enabled", "logo", "updated_at")}),)
