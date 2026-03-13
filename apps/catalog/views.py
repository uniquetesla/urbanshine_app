from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.db.models import F, Q
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from apps.accounts.models import UserRole

from .forms import ArticleForm
from .models import Article, GoodsReceipt


class EmployeeOnlyMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role != UserRole.STAMMKUNDE


class ArticleListView(LoginRequiredMixin, ListView):
    model = Article
    template_name = "catalog/article_list.html"
    context_object_name = "articles"

    def get_queryset(self):
        queryset = Article.objects.order_by("name")
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query)
                | Q(kategorie__icontains=query)
                | Q(icon__icontains=query)
                | Q(beschreibung__icontains=query)
                | Q(barcode__icontains=query)
                | Q(artikelnummer__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "").strip()
        return context


class ArticleCreateView(EmployeeOnlyMixin, LoginRequiredMixin, CreateView):
    model = Article
    form_class = ArticleForm
    template_name = "catalog/article_form.html"
    success_url = reverse_lazy("catalog:article_list")

    def form_valid(self, form):
        messages.success(self.request, "Artikel wurde erfolgreich angelegt.")
        return super().form_valid(form)


class ArticleUpdateView(EmployeeOnlyMixin, LoginRequiredMixin, UpdateView):
    model = Article
    form_class = ArticleForm
    template_name = "catalog/article_form.html"
    success_url = reverse_lazy("catalog:article_list")

    def form_valid(self, form):
        messages.success(self.request, "Artikel wurde erfolgreich aktualisiert.")
        return super().form_valid(form)


class ArticleDeleteView(EmployeeOnlyMixin, LoginRequiredMixin, DeleteView):
    model = Article
    template_name = "catalog/article_confirm_delete.html"
    success_url = reverse_lazy("catalog:article_list")

    def form_valid(self, form):
        messages.success(self.request, "Artikel wurde erfolgreich gelöscht.")
        return super().form_valid(form)


class GoodsReceiptView(EmployeeOnlyMixin, LoginRequiredMixin, TemplateView):
    template_name = "catalog/goods_receipt.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["receipts"] = GoodsReceipt.objects.select_related("artikel", "gebucht_von")[:30]
        return context


class GoodsReceiptLookupView(EmployeeOnlyMixin, LoginRequiredMixin, View):
    def post(self, request, *_args, **_kwargs):
        code = (request.POST.get("code") or "").strip()
        if not code:
            return JsonResponse({"ok": False, "message": "Bitte Barcode oder Artikelnummer scannen."}, status=400)

        query = Q(barcode__iexact=code)
        if code.isdigit():
            query |= Q(artikelnummer=int(code))

        article = Article.objects.filter(query).order_by("id").first()
        if not article:
            return JsonResponse({"ok": False, "message": "Kein Artikel mit dieser Nummer gefunden."}, status=404)

        return JsonResponse(
            {
                "ok": True,
                "article": {
                    "id": article.pk,
                    "name": article.name,
                    "artikelnummer": article.formatted_artikelnummer,
                    "barcode": article.barcode or "-",
                    "stock": article.lagerbestand,
                },
            }
        )


class GoodsReceiptBookView(EmployeeOnlyMixin, LoginRequiredMixin, View):
    def post(self, request, *_args, **_kwargs):
        article_id = request.POST.get("article_id")
        try:
            qty = int(request.POST.get("menge") or 0)
        except ValueError:
            qty = 0
        note = (request.POST.get("notiz") or "").strip()

        if qty <= 0:
            return JsonResponse({"ok": False, "message": "Bitte eine gültige Menge angeben."}, status=400)

        article = Article.objects.filter(pk=article_id).first()
        if not article:
            return JsonResponse({"ok": False, "message": "Artikel wurde nicht gefunden."}, status=404)

        with transaction.atomic():
            Article.objects.filter(pk=article.pk).update(lagerbestand=F("lagerbestand") + qty)
            article.refresh_from_db(fields=["lagerbestand", "artikelnummer", "barcode", "name"])
            GoodsReceipt.objects.create(
                artikel=article,
                artikelnummer=article.formatted_artikelnummer,
                barcode=article.barcode or "",
                menge=qty,
                notiz=note,
                gebucht_von=request.user,
            )

        return JsonResponse(
            {
                "ok": True,
                "message": f"Wareneingang gebucht: {article.name} +{qty}. Neuer Bestand: {article.lagerbestand}.",
                "stock": article.lagerbestand,
            }
        )
