# Generated by Django 3.1.6 on 2021-11-07 09:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0002_shopfeature_is_publish'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shopfeatureinvoice',
            name='feature',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shop_feature_invoices', to='shop.shopfeature', verbose_name='ویژگی فروشگاه'),
        ),
        migrations.AlterField(
            model_name='shopfeatureinvoice',
            name='payment_datetime',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='تاریخ خرید'),
        ),
    ]
