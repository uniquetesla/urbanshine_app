from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import F, Q
from django.shortcuts import redirect
from django.views.generic import TemplateView

from apps.catalog.models import Article

from .models import PaymentMethod, Sale, SaleItem


class CheckoutView(LoginRequiredMixin, TemplateView):
    template_name = "checkout/pos.html"
    cart_session_key = "checkout_cart"

    def get(self, request, *args, **kwargs):
        if request.GET.get("clear") == "1":
            request.session[self.cart_session_key] = {}
            request.session.modified = True
            messages.success(request, "Warenkorb wurde geleert.")
            return redirect("checkout:pos")
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        article_id = request.POST.get("article_id")
        quantity = self._safe_positive_int(request.POST.get("quantity"), default=1)

        if action == "add" and article_id:
            self._add_to_cart(article_id, quantity)
            messages.success(request, "Artikel wurde dem Warenkorb hinzugefügt.")
            return redirect("checkout:pos")

        if action == "update" and article_id:
            self._update_cart_item(article_id, quantity)
            messages.success(request, "Menge wurde aktualisiert.")
            return redirect("checkout:pos")

        if action == "remove" and article_id:
            self._remove_from_cart(article_id)
            messages.success(request, "Artikel wurde aus dem Warenkorb entfernt.")
            return redirect("checkout:pos")

        if action == "checkout":
            payment_method = request.POST.get("payment_method")
            self._finalize_sale(payment_method)
            return redirect("checkout:pos")

        messages.error(request, "Unbekannte Aktion.")
        return redirect("checkout:pos")

    def _add_to_cart(self, article_id, quantity):
        cart = self._get_cart()
        current = cart.get(article_id, 0)
        cart[article_id] = current + quantity
        self.request.session[self.cart_session_key] = cart
        self.request.session.modified = True

    def _update_cart_item(self, article_id, quantity):
        cart = self._get_cart()
        if quantity <= 0:
            cart.pop(article_id, None)
        else:
            cart[article_id] = quantity
        self.request.session[self.cart_session_key] = cart
        self.request.session.modified = True

    def _remove_from_cart(self, article_id):
        cart = self._get_cart()
        cart.pop(article_id, None)
        self.request.session[self.cart_session_key] = cart
        self.request.session.modified = True

    def _finalize_sale(self, payment_method):
        cart = self._get_cart()
        if not cart:
            messages.error(self.request, "Der Warenkorb ist leer.")
            return
        if payment_method not in dict(PaymentMethod.choices):
            messages.error(self.request, "Bitte eine gültige Zahlungsart wählen.")
            return

        article_ids = [int(article_id) for article_id in cart.keys()]
        with transaction.atomic():
            articles = {
                article.id: article
                for article in Article.objects.select_for_update().filter(id__in=article_ids)
            }
            for article_id, qty in cart.items():
                article = articles.get(int(article_id))
                if not article:
                    messages.error(self.request, "Ein Artikel im Warenkorb existiert nicht mehr.")
                    return
                if article.lagerbestand < qty:
                    messages.error(
                        self.request,
                        f"Nicht genug Bestand für {article.name}. Verfügbar: {article.lagerbestand}.",
                    )
                    return

            sale = Sale.objects.create(mitarbeiter=self.request.user, zahlungsart=payment_method)
            total = Decimal("0.00")
            for article_id, qty in cart.items():
                article = articles[int(article_id)]
                line_total = article.preis * qty
                SaleItem.objects.create(
                    verkauf=sale,
                    artikel=article,
                    menge=qty,
                    einzelpreis=article.preis,
                    gesamtpreis=line_total,
                )
                Article.objects.filter(pk=article.pk).update(lagerbestand=F("lagerbestand") - qty)
                total += line_total

            sale.gesamtbetrag = total
            sale.save(update_fields=["gesamtbetrag"])

        self.request.session[self.cart_session_key] = {}
        self.request.session.modified = True
        messages.success(self.request, f"Verkauf #{sale.verkaufsnummer} wurde gespeichert.")

    def _get_cart(self):
        return self.request.session.get(self.cart_session_key, {})

    @staticmethod
    def _safe_positive_int(raw_value, default=1):
        try:
            value = int(raw_value)
        except (TypeError, ValueError):
            return default
        return max(value, 0)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("q", "").strip()

        article_queryset = Article.objects.order_by("name")
        if query:
            article_queryset = article_queryset.filter(
                Q(name__icontains=query) | Q(kategorie__icontains=query) | Q(beschreibung__icontains=query)
            )

        cart = self._get_cart()
        cart_article_ids = [int(article_id) for article_id in cart.keys()]
        cart_articles = {article.id: article for article in Article.objects.filter(id__in=cart_article_ids)}

        cart_items = []
        total = Decimal("0.00")
        for article_id, qty in cart.items():
            article = cart_articles.get(int(article_id))
            if not article:
                continue
            line_total = article.preis * qty
            total += line_total
            cart_items.append({"article": article, "quantity": qty, "line_total": line_total})

        context.update(
            {
                "query": query,
                "articles": article_queryset,
                "cart_items": cart_items,
                "cart_total": total,
                "payment_methods": PaymentMethod.choices,
            }
        )
        return context
