from django.urls import path

from .views import AppointmentOverviewView

app_name = "scheduling"

urlpatterns = [
    path("", AppointmentOverviewView.as_view(), name="appointment_overview"),
]
