from django.urls import path

from .views import MasterDataDeleteView, MasterDataUpdateView, MasterDataView

app_name = "company"

urlpatterns = [
    path("stammdaten/", MasterDataView.as_view(), name="master_data"),
    path("stammdaten/<str:model_name>/<int:pk>/bearbeiten/", MasterDataUpdateView.as_view(), name="master_data_update"),
    path("stammdaten/<str:model_name>/<int:pk>/delete/", MasterDataDeleteView.as_view(), name="master_data_delete"),
]
