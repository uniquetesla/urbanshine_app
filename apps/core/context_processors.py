from apps.company.models import CompanySettings


def company_branding(_request):
    settings = CompanySettings.objects.order_by("pk").first()
    return {"company_settings": settings}
