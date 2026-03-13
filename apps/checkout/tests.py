from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User, UserRole
from apps.catalog.models import Article
from apps.checkout.models import PaymentMethod, Sale, SaleItem
from apps.customers.models import Customer
from apps.invoices.models import Invoice


class CheckoutInvoiceFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="kasse", password="pass123", role=UserRole.ADMIN)
        self.client.force_login(self.user)
        self.customer = Customer.objects.create(
            vorname="Karl",
            nachname="Kunde",
            strasse="Teststraße",
            hausnummer="3",
            plz="12345",
            ort="Musterstadt",
            email="karl@example.com",
        )

    def _create_article(self, name="Shampoo", price="15.00"):
        return Article.objects.create(
            name=name,
            kategorie="Pflege",
            icon=Article.ICON_INNENREINIGER,
            preis=price,
            lagerbestand=20,
        )

    def test_create_invoice_for_sale(self):
        article = self._create_article()
        sale = Sale.objects.create(mitarbeiter=self.user, kunde=self.customer, zahlungsart=PaymentMethod.RECHNUNG, gesamtbetrag="30.00")
        SaleItem.objects.create(verkauf=sale, artikel=article, menge=2, einzelpreis="15.00", gesamtpreis="30.00")

        response = self.client.post(reverse("checkout:sale_create_invoice", kwargs={"pk": sale.pk}))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Invoice.objects.filter(verkauf=sale).count(), 1)

        self.client.post(reverse("checkout:sale_create_invoice", kwargs={"pk": sale.pk}))
        self.assertEqual(Invoice.objects.filter(verkauf=sale).count(), 1)

    def test_checkout_creates_invoice_automatically(self):
        article = self._create_article(name="Wachs", price="10.00")
        session = self.client.session
        session["checkout_cart"] = {str(article.id): 3}
        session.save()

        response = self.client.post(
            reverse("checkout:pos"),
            data={
                "action": "checkout",
                "payment_method": PaymentMethod.RECHNUNG,
                "customer_search": f"{self.customer.formatted_kundennummer} · {self.customer.vorname} {self.customer.nachname}",
            },
        )

        self.assertEqual(response.status_code, 302)
        sale = Sale.objects.get()
        self.assertEqual(Invoice.objects.filter(verkauf=sale).count(), 1)
