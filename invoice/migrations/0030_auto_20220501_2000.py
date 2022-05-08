# Generated by Django 3.1.6 on 2022-05-01 15:30

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

def create_dummy_product(apps, schema_editor):
    Product = apps.get_model("nakhll_market", "Product")
    Shop = apps.get_model("nakhll_market", "Shop")
    Product.objects.create(
        Title = 'dummy',
        FK_Shop = Shop.objects.get(Title='dummy'),
        Available = False,
        Publish = False,
        Price = 0,
        OldPrice = 0,
        Inventory = 0,
    )


def invoice_without_user(apps, schema_editor):
    User = apps.get_model("auth", "User")
    Invoice = apps.get_model("invoice", "Invoice")
    dummy_user = User.objects.get(username="dummy")
    invoices = Invoice.objects.filter(user=None)
    for invoice in invoices:
        invoice.user = dummy_user
        invoice.save()


def invoiceitem_without_product(apps, schema_editor):
    InvoiceItem = apps.get_model("invoice", "InvoiceItem")
    Product = apps.get_model("nakhll_market", "Product")
    dummy_product = Product.objects.get(Title='dummy')
    invoiceitems = InvoiceItem.objects.filter(product=None)
    for invoiceitem in invoiceitems:
        invoiceitem.product = dummy_product
        invoiceitem.save()


class Migration(migrations.Migration):

    dependencies = [
        ('invoice', '0029_remove_invoice_address'),
    ]

    operations = [
        migrations.RunPython(create_dummy_product, migrations.RunPython.noop),
        migrations.RunPython(invoice_without_user, migrations.RunPython.noop),
        migrations.RunPython(invoiceitem_without_product, migrations.RunPython.noop),
    ]
