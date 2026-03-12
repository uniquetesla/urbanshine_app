from django.urls import path

from .views import (
    OrderCreateView,
    OrderDeleteView,
    OrderDetailView,
    OrderListView,
    OrderQuickStatusUpdateView,
    OrderUpdateView,
)

app_name = "orders"

urlpatterns = [
    path("", OrderListView.as_view(), name="order_list"),
    path("neu/", OrderCreateView.as_view(), name="order_create"),
    path("<int:pk>/", OrderDetailView.as_view(), name="order_detail"),
    path("<int:pk>/status/", OrderQuickStatusUpdateView.as_view(), name="order_quick_status"),
    path("<int:pk>/bearbeiten/", OrderUpdateView.as_view(), name="order_update"),
    path("<int:pk>/loeschen/", OrderDeleteView.as_view(), name="order_delete"),
]
