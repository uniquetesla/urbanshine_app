from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.db.models import F, Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from apps.accounts.models import UserRole

from .forms import ArticleForm, GoodsReceiptForm
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

    def post(self, request, *args, **kwargs):
        form = GoodsReceiptForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Bitte Barcode und Menge korrekt eingeben.")
            return self.render_to_response(self.get_context_data(form=form))

        barcode = form.cleaned_data["barcode"]
        qty = form.cleaned_data["menge"]
        note = form.cleaned_data["notiz"]
        article = Article.objects.filter(barcode=barcode).first()

        if not article:
            messages.error(request, "Kein Artikel mit diesem Barcode gefunden.")
            return self.render_to_response(self.get_context_data(form=form))

        with transaction.atomic():
            Article.objects.filter(pk=article.pk).update(lagerbestand=F("lagerbestand") + qty)
            article.refresh_from_db(fields=["lagerbestand", "artikelnummer", "barcode", "name"])
            GoodsReceipt.objects.create(
                artikel=article,
                artikelnummer=article.formatted_artikelnummer,
                barcode=article.barcode,
                menge=qty,
                notiz=note,
                gebucht_von=request.user,
            )

        messages.success(request, f"Wareneingang gebucht: {article.name} +{qty}. Neuer Bestand: {article.lagerbestand}.")
        return self.render_to_response(self.get_context_data(form=GoodsReceiptForm()))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = kwargs.get("form") or GoodsReceiptForm()
        context["receipts"] = GoodsReceipt.objects.select_related("artikel", "gebucht_von")[:30]
        return context
