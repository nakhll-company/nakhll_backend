# Generated by Django 3.1.6 on 2021-10-18 10:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('invoice', '0024_invoiceitem_barcode'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='invoice',
            options={'ordering': ('-id',), 'verbose_name': 'فاکتور', 'verbose_name_plural': 'فاکتورها'},
        ),
        migrations.AlterModelOptions(
            name='invoiceitem',
            options={'verbose_name': 'آیتم فاکتور', 'verbose_name_plural': 'آیتم های فاکتور'},
        ),
    ]
