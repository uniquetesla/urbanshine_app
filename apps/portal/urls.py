from django.urls import path

from .views import CustomerPortalView

app_name = "portal"

urlpatterns = [
    path("", CustomerPortalView.as_view(), name="dashboard"),
]
