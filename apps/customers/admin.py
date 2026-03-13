from django.contrib import admin

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("formatted_kundennummer", "vorname", "nachname", "ort", "telefon", "email")
    list_filter = ("ort",)
    search_fields = ("vorname", "nachname", "telefon", "email", "ort")

    @admin.display(description="Kundennummer", ordering="kundennummer")
    def formatted_kundennummer(self, obj):
        return obj.formatted_kundennummer
