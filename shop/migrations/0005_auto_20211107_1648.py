# Generated by Django 3.1.6 on 2021-11-07 13:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0004_shoplanding'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shoplanding',
            name='page_data',
            field=models.TextField(blank=True, null=True, verbose_name='داده\u200cهای صفحه'),
        ),
    ]
