# Generated by Django 3.1.6 on 2021-10-01 17:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coupon', '0006_couponconstraint_extra_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='couponconstraint',
            name='max_purchase_amount',
            field=models.BigIntegerField(blank=True, null=True, verbose_name='حداکثر مقدار خرید'),
        ),
        migrations.AlterField(
            model_name='couponconstraint',
            name='min_purchase_amount',
            field=models.BigIntegerField(blank=True, null=True, verbose_name='حداقل مقدار خرید'),
        ),
    ]
