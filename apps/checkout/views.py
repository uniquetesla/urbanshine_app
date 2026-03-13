from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.db.models import F, Q
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import TemplateView

from apps.accounts.models import UserRole
from apps.catalog.models import Article
from apps.customers.models import Customer
from apps.core.number_sequences import parse_sequence_value
from apps.invoices.services import create_invoice_for_sale

from .models import PaymentMethod, Sale, SaleItem


class EmployeeOnlyMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role != UserRole.STAMMKUNDE


class CheckoutView(EmployeeOnlyMixin, LoginRequiredMixin, TemplateView):
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

        if action == "scan":
            barcode = (request.POST.get("barcode") or "").strip()
            if not barcode:
                messages.error(request, "Bitte Barcode eingeben.")
                return redirect("checkout:pos")
            article = Article.objects.filter(barcode=barcode).first()
            if not article:
                messages.error(request, "Kein Artikel zu diesem Barcode gefunden.")
                return redirect("checkout:pos")
            self._add_to_cart(str(article.id), 1)
            messages.success(request, f"{article.name} wurde per Barcode hinzugefügt.")
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
            customer_search = request.POST.get("customer_search", "")
            self._finalize_sale(payment_method, customer_search)
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

    def _finalize_sale(self, payment_method, customer_search):
        cart = self._get_cart()
        if not cart:
            messages.error(self.request, "Der Warenkorb ist leer.")
            return
        if payment_method not in dict(PaymentMethod.choices):
            messages.error(self.request, "Bitte eine gültige Zahlungsart wählen.")
            return

        customer = self._resolve_customer(customer_search)
        if not customer:
            messages.error(self.request, "Bitte einen gültigen Kunden auswählen.")
            return

        article_ids = [int(article_id) for article_id in cart.keys()]
        invoice = None
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

            sale = Sale.objects.create(mitarbeiter=self.request.user, kunde=customer, zahlungsart=payment_method)
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
            invoice = create_invoice_for_sale(sale) if sale.kunde else None

        self.request.session[self.cart_session_key] = {}
        self.request.session.modified = True
        if invoice:
            messages.success(
                self.request,
                f"Verkauf #{sale.verkaufsnummer} wurde gespeichert. Rechnung {invoice.formatted_rechnungsnummer} wurde erstellt.",
            )
        else:
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

    @staticmethod
    def _resolve_customer(value):
        value = (value or "").strip()
        if not value:
            return None

        kundennummer_raw = value.split("·", 1)[0].strip()
        kundennummer = parse_sequence_value(kundennummer_raw)
        if kundennummer is not None:
            customer = Customer.objects.filter(kundennummer=kundennummer).first()
            if customer:
                return customer

        if " " in value:
            vorname, nachname = value.split(" ", 1)
            return Customer.objects.filter(vorname__iexact=vorname, nachname__iexact=nachname).first()
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("q", "").strip()

        article_queryset = Article.objects.order_by("name")
        if query:
            article_queryset = article_queryset.filter(
                Q(name__icontains=query)
                | Q(kategorie__icontains=query)
                | Q(beschreibung__icontains=query)
                | Q(barcode__icontains=query)
                | Q(artikelnummer__icontains=query)
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

        sales_queryset = Sale.objects.select_related("kunde", "mitarbeiter").prefetch_related("positionen__artikel")[:20]
        sales = [
            {"sale": sale, "invoice": getattr(sale, "rechnung", None)}
            for sale in sales_queryset
        ]

        context.update(
            {
                "query": query,
                "articles": article_queryset,
                "cart_items": cart_items,
                "cart_total": total,
                "payment_methods": PaymentMethod.choices,
                "customer_suggestions": [
                    f"{customer.formatted_kundennummer} · {customer.vorname} {customer.nachname}"
                    for customer in Customer.objects.order_by("nachname", "vorname")
                ],
                "sales": sales,
            }
        )
        return context


class SaleCreateInvoiceView(EmployeeOnlyMixin, LoginRequiredMixin, View):
    def post(self, request, pk):
        sale = get_object_or_404(Sale.objects.select_related("kunde"), pk=pk)
        existing_invoice = getattr(sale, "rechnung", None)
        if existing_invoice:
            messages.info(request, f"Für Verkauf #{sale.verkaufsnummer} existiert bereits eine Rechnung.")
            return redirect("checkout:pos")

        invoice = create_invoice_for_sale(sale)
        if not invoice:
            messages.error(request, "Für diesen Verkauf konnte keine Rechnung erstellt werden.")
            return redirect("checkout:pos")

        messages.success(request, f"Rechnung {invoice.formatted_rechnungsnummer} für Verkauf #{sale.verkaufsnummer} erstellt.")
        return redirect("checkout:pos")
