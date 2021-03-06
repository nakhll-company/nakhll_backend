# Generated by Django 3.1.6 on 2021-10-03 17:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoice', '0010_auto_20211003_1853'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='invoice',
            name='invoice_price',
        ),
        migrations.AddField(
            model_name='invoice',
            name='invoice_price_with_discount',
            field=models.DecimalField(decimal_places=0, default=0, max_digits=12, verbose_name='مبلغ فاکتور با تخفیف'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='invoice_price_without_discount',
            field=models.DecimalField(decimal_places=0, default=0, max_digits=12, verbose_name='مبلغ فاکتور بدون تخفیف'),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='coupon_price',
            field=models.DecimalField(decimal_places=0, default=0, max_digits=12, verbose_name='مبلغ کوپن'),
        ),
    ]
