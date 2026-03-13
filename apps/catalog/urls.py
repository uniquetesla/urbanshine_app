from django.urls import path

from .views import ArticleCreateView, ArticleDeleteView, ArticleListView, ArticleUpdateView, GoodsReceiptView

app_name = "catalog"

urlpatterns = [
    path("", ArticleListView.as_view(), name="article_list"),
    path("neu/", ArticleCreateView.as_view(), name="article_create"),
    path("wareneingang/", GoodsReceiptView.as_view(), name="goods_receipt"),
    path("<int:pk>/bearbeiten/", ArticleUpdateView.as_view(), name="article_update"),
    path("<int:pk>/loeschen/", ArticleDeleteView.as_view(), name="article_delete"),
]
