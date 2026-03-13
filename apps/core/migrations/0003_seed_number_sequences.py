from django.db import migrations
from django.db.models import Max


def seed_sequences(apps, schema_editor):
    NumberSequence = apps.get_model("core", "NumberSequence")
    Customer = apps.get_model("customers", "Customer")
    Order = apps.get_model("orders", "Order")
    Invoice = apps.get_model("invoices", "Invoice")
    Offer = apps.get_model("offers", "Offer")
    Article = apps.get_model("catalog", "Article")

    config = {
        "auftrag": ("AUF", "-", Order.objects.aggregate(m=Max("auftragsnummer"))["m"] or 0),
        "kunde": ("KUN", "-", Customer.objects.aggregate(m=Max("kundennummer"))["m"] or 0),
        "rechnung": ("RE", "-", Invoice.objects.aggregate(m=Max("rechnungsnummer"))["m"] or 0),
        "angebot": ("ANG", "-", Offer.objects.aggregate(m=Max("angebotsnummer"))["m"] or 0),
        "artikel": ("ART", "-", Article.objects.aggregate(m=Max("artikelnummer"))["m"] or 0),
    }

    for sequence_type, (prefix, separator, last_value) in config.items():
        NumberSequence.objects.update_or_create(
            sequence_type=sequence_type,
            defaults={
                "prefix": prefix,
                "separator": separator,
                "start_value": 1,
                "padding": 5,
                "last_value": last_value,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_numbersequence"),
        ("customers", "0001_initial"),
        ("orders", "0002_alter_orderimage_options_and_more"),
        ("invoices", "0003_invoice_verkauf_invoice_unique_invoice_per_order"),
        ("offers", "0001_initial"),
        ("catalog", "0003_populate_article_identifiers"),
    ]

    operations = [
        migrations.RunPython(seed_sequences, migrations.RunPython.noop),
    ]
