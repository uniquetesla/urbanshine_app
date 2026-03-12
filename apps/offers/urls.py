from django.urls import path

from .views import OfferConvertToOrderView, OfferCreateView, OfferDetailView, OfferListView

app_name = "offers"

urlpatterns = [
    path("", OfferListView.as_view(), name="offer_list"),
    path("neu/", OfferCreateView.as_view(), name="offer_create"),
    path("<int:pk>/", OfferDetailView.as_view(), name="offer_detail"),
    path("<int:pk>/umwandeln/", OfferConvertToOrderView.as_view(), name="offer_convert"),
]
