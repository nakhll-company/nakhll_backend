# Generated by Django 3.1.6 on 2021-10-03 09:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nakhll_market', '0108_auto_20210918_1650'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='post_range_cities',
            field=models.ManyToManyField(related_name='products', to='nakhll_market.City', verbose_name='شهرهای قابل ارسال'),
        ),
    ]
