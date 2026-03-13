from django.urls import path

from .views import (
    CompanySettingsDetailView,
    CompanySettingsUpdateView,
    MasterDataModuleCreateView,
    MasterDataModuleDeleteView,
    MasterDataModuleDetailView,
    MasterDataModuleListView,
    MasterDataModuleUpdateView,
    MasterDataView,
)

app_name = "company"

urlpatterns = [
    path("stammdaten/", MasterDataView.as_view(), name="master_data"),
    path("stammdaten/firma/", CompanySettingsDetailView.as_view(), name="company_settings_detail"),
    path("stammdaten/firma/bearbeiten/", CompanySettingsUpdateView.as_view(), name="company_settings_update"),
    path("stammdaten/<str:module>/", MasterDataModuleListView.as_view(), name="master_data_module_list"),
    path("stammdaten/<str:module>/neu/", MasterDataModuleCreateView.as_view(), name="master_data_module_create"),
    path("stammdaten/<str:module>/<int:pk>/", MasterDataModuleDetailView.as_view(), name="master_data_module_detail"),
    path("stammdaten/<str:module>/<int:pk>/bearbeiten/", MasterDataModuleUpdateView.as_view(), name="master_data_module_update"),
    path("stammdaten/<str:module>/<int:pk>/loeschen/", MasterDataModuleDeleteView.as_view(), name="master_data_module_delete"),
]
