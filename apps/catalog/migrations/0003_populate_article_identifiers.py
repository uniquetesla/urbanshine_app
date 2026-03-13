from django.db import migrations


def populate_article_identifiers(apps, schema_editor):
    Article = apps.get_model("catalog", "Article")
    for idx, article in enumerate(Article.objects.order_by("id"), start=1):
        changed = False
        if not article.artikelnummer:
            article.artikelnummer = idx
            changed = True
        if not article.barcode:
            article.barcode = f"AUTO-{article.id}"
            changed = True
        if changed:
            article.save(update_fields=["artikelnummer", "barcode"])


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0002_article_artikelnummer_article_barcode_goodsreceipt"),
    ]

    operations = [
        migrations.RunPython(populate_article_identifiers, migrations.RunPython.noop),
    ]
