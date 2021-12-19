# Generated by Django 3.1.6 on 2021-12-19 09:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logistic', '0008_auto_20211218_1319'),
    ]

    operations = [
        migrations.AlterField(
            model_name='logisticunitmetric',
            name='price_per_extra_kg',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='قیمت هر کیلوگرم اضافه'),
        ),
        migrations.AlterField(
            model_name='logisticunitmetric',
            name='price_per_kg',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='قیمت هر کیلوگرم'),
        ),
    ]
