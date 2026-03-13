from django.contrib import admin

from .models import Article, GoodsReceipt


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("formatted_artikelnummer", "barcode", "name", "kategorie", "einheit", "preis", "lagerbestand", "icon")
    list_filter = ("kategorie", "icon", "einheit")
    search_fields = ("artikelnummer", "barcode", "name", "kategorie", "beschreibung", "einheit")
    list_editable = ("einheit", "preis", "lagerbestand")


@admin.register(GoodsReceipt)
class GoodsReceiptAdmin(admin.ModelAdmin):
    list_display = ("created_at", "artikel", "artikelnummer", "barcode", "menge", "gebucht_von")
    search_fields = ("artikelnummer", "barcode", "artikel__name")
    list_filter = ("created_at", "gebucht_von")
