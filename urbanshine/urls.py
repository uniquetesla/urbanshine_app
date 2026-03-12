from django.contrib import admin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import include, path


def healthcheck(_request):
    return JsonResponse({"status": "ok", "service": "urbanshine"})


def root_redirect(_request):
    return redirect("accounts:dashboard")


urlpatterns = [
    path("", root_redirect, name="root"),
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("kunden/", include("apps.customers.urls")),
    path("", include("apps.company.urls")),
    path("health/", healthcheck, name="healthcheck"),
]
