from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import include, path


def healthcheck(_request):
    return JsonResponse({"status": "ok", "service": "urbanshine"})


def root_redirect(_request):
    return redirect("accounts:dashboard")


def has_internal_admin_user():
    user_model = get_user_model()
    return user_model.objects.filter(role="admin", is_active=True).exists()


def admin_login_redirect(request):
    if has_internal_admin_user():
        return redirect("accounts:login")
    return admin.site.login(request)


urlpatterns = [
    path("", root_redirect, name="root"),
    path("admin/login/", admin_login_redirect, name="admin_login_redirect"),
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("kunden/", include("apps.customers.urls")),
    path("auftraege/", include("apps.orders.urls")),
    path("artikel/", include("apps.catalog.urls")),
    path("kasse/", include("apps.checkout.urls")),
    path("mitarbeiter/", include("apps.employees.urls")),
    path("termine/", include("apps.scheduling.urls")),
    path("rechnungen/", include("apps.invoices.urls")),
    path("angebote/", include("apps.offers.urls")),
    path("dokumente/", include("apps.documents.urls")),
    path("portal/", include("apps.portal.urls")),
    path("", include("apps.company.urls")),
    path("health/", healthcheck, name="healthcheck"),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
