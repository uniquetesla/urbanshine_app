from django.contrib import admin

from .models import CompanySettings, OrderType, Price, Service, SoilingLevel, Surcharge


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "estimated_duration_minutes", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(Price)
class PriceAdmin(admin.ModelAdmin):
    list_display = ("name", "amount", "unit", "is_active")
    list_filter = ("is_active",)


@admin.register(OrderType)
class OrderTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)


@admin.register(SoilingLevel)
class SoilingLevelAdmin(admin.ModelAdmin):
    list_display = ("name", "multiplier", "is_active")
    list_filter = ("is_active",)


@admin.register(Surcharge)
class SurchargeAdmin(admin.ModelAdmin):
    list_display = ("name", "amount", "is_percentage", "is_active")
    list_filter = ("is_active", "is_percentage")


@admin.register(CompanySettings)
class CompanySettingsAdmin(admin.ModelAdmin):
    list_display = ("company_name", "email", "invoice_generation_enabled", "updated_at")
