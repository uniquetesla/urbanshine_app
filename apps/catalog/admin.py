from django.contrib import admin

from .models import Article


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("name", "kategorie", "preis", "lagerbestand", "icon")
    list_filter = ("kategorie", "icon")
    search_fields = ("name", "kategorie", "beschreibung")
