# Generated by Django 3.2.12 on 2022-05-18 07:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('nakhll_market', '0147_manipulate_null_category'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.ForeignKey(db_column='category_id', on_delete=django.db.models.deletion.PROTECT, related_name='products', to='nakhll_market.category', verbose_name='دسته بندی جدید'),
        ),
    ]
