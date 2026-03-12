from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import ArticleForm
from .models import Article


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
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "").strip()
        return context


class ArticleCreateView(LoginRequiredMixin, CreateView):
    model = Article
    form_class = ArticleForm
    template_name = "catalog/article_form.html"
    success_url = reverse_lazy("catalog:article_list")

    def form_valid(self, form):
        messages.success(self.request, "Artikel wurde erfolgreich angelegt.")
        return super().form_valid(form)


class ArticleUpdateView(LoginRequiredMixin, UpdateView):
    model = Article
    form_class = ArticleForm
    template_name = "catalog/article_form.html"
    success_url = reverse_lazy("catalog:article_list")

    def form_valid(self, form):
        messages.success(self.request, "Artikel wurde erfolgreich aktualisiert.")
        return super().form_valid(form)


class ArticleDeleteView(LoginRequiredMixin, DeleteView):
    model = Article
    template_name = "catalog/article_confirm_delete.html"
    success_url = reverse_lazy("catalog:article_list")

    def form_valid(self, form):
        messages.success(self.request, "Artikel wurde erfolgreich gelöscht.")
        return super().form_valid(form)
