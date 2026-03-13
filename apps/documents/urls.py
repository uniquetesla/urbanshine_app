from django.urls import path

from .views import (
    DocumentBulkZipDownloadView,
    DocumentCreateView,
    DocumentDeleteView,
    DocumentDetailView,
    DocumentDownloadView,
    DocumentListView,
    DocumentUpdateView,
)

app_name = "documents"

urlpatterns = [
    path("", DocumentListView.as_view(), name="document_list"),
    path("neu/", DocumentCreateView.as_view(), name="document_create"),
    path("zip-download/", DocumentBulkZipDownloadView.as_view(), name="document_bulk_download"),
    path("<int:pk>/", DocumentDetailView.as_view(), name="document_detail"),
    path("<int:pk>/download/", DocumentDownloadView.as_view(), name="document_download"),
    path("<int:pk>/bearbeiten/", DocumentUpdateView.as_view(), name="document_update"),
    path("<int:pk>/loeschen/", DocumentDeleteView.as_view(), name="document_delete"),
]
