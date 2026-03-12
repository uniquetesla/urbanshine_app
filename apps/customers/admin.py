from django.contrib import admin

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("kundennummer", "vorname", "nachname", "ort", "telefon", "email")
    list_filter = ("ort",)
    search_fields = ("kundennummer", "vorname", "nachname", "telefon", "email", "ort")
