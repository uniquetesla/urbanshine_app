from django.urls import path

from .views import (
    ArticleCreateView,
    ArticleDetailView,
    ArticleDeleteView,
    ArticleListView,
    ArticleUpdateView,
    GoodsReceiptBookView,
    GoodsReceiptLookupView,
    GoodsReceiptView,
)

app_name = "catalog"

urlpatterns = [
    path("", ArticleListView.as_view(), name="article_list"),
    path("neu/", ArticleCreateView.as_view(), name="article_create"),
    path("<int:pk>/", ArticleDetailView.as_view(), name="article_detail"),
    path("wareneingang/", GoodsReceiptView.as_view(), name="goods_receipt"),
    path("wareneingang/suche/", GoodsReceiptLookupView.as_view(), name="goods_receipt_lookup"),
    path("wareneingang/buchen/", GoodsReceiptBookView.as_view(), name="goods_receipt_book"),
    path("<int:pk>/bearbeiten/", ArticleUpdateView.as_view(), name="article_update"),
    path("<int:pk>/loeschen/", ArticleDeleteView.as_view(), name="article_delete"),
]
