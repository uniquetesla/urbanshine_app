from django.urls import path

from .views import (
    CustomerCreateView,
    CustomerDeleteView,
    CustomerDetailView,
    CustomerListView,
    CustomerUpdateView,
)

app_name = "customers"

urlpatterns = [
    path("", CustomerListView.as_view(), name="customer_list"),
    path("neu/", CustomerCreateView.as_view(), name="customer_create"),
    path("<int:pk>/", CustomerDetailView.as_view(), name="customer_detail"),
    path("<int:pk>/bearbeiten/", CustomerUpdateView.as_view(), name="customer_update"),
    path("<int:pk>/loeschen/", CustomerDeleteView.as_view(), name="customer_delete"),
]
