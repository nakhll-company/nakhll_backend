# Generated by Django 3.1.6 on 2022-01-05 07:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nakhll_market', '0135_auto_20211205_1607'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalproduct',
            name='Inventory',
            field=models.PositiveIntegerField(default=5, verbose_name='میزان موجودی از این کالا در انبار'),
        ),
        migrations.AlterField(
            model_name='product',
            name='Inventory',
            field=models.PositiveIntegerField(default=5, verbose_name='میزان موجودی از این کالا در انبار'),
        ),
    ]
