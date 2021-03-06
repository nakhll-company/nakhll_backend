# Generated by Django 3.1.6 on 2021-10-09 12:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nakhll_market', '0119_merge_20211009_1528'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='landingpageschema',
            name='device',
        ),
        migrations.RemoveField(
            model_name='product',
            name='barcode',
        ),
        migrations.RemoveField(
            model_name='shop',
            name='has_product_group_import_permission',
        ),
        migrations.RemoveField(
            model_name='shop',
            name='is_landing',
        ),
        migrations.AddField(
            model_name='landingpageschema',
            name='is_mobile',
            field=models.BooleanField(default=True, verbose_name='دستگاه موبایل است؟'),
        ),
    ]
