# Generated by Django 3.1.6 on 2021-10-08 17:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoice', '0021_invoiceitem_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='logistic_price',
            field=models.DecimalField(decimal_places=0, default=0, max_digits=12, verbose_name='هزینه حمل و نقل'),
        ),
    ]
