# Generated by Django 3.1.6 on 2021-10-06 12:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounting_new', '0020_remove_invoice_coupon_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoiceitem',
            name='slug',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
    ]
