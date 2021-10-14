# Generated by Django 3.1.5 on 2021-02-06 14:51

from nakhll_market.models import Product, ProductMovie
from django.db import migrations, models

def make_int(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    products = Product.objects.all()
    for product in products:
        try:
            product.Price = int(product.Price)
        except:
            product.Price = 0
            product.Publish = False
            product.Available = False
        try:
            product.OldPrice = int(product.OldPrice)
        except:
            product.OldPrice = 0
            product.Publish = False
            product.Available = False
        product.save()

class Migration(migrations.Migration):

    dependencies = [
        ('nakhll_market', '0080_profile_imagenationalcard'),
    ]

    operations = [
        # migrations.RunPython(make_int),
        migrations.AlterField(
            model_name='product',
            name='OldPrice',
            field=models.BigIntegerField(default=0, verbose_name='قیمت حذف محصول'),
        ),
        migrations.AlterField(
            model_name='product',
            name='Price',
            field=models.BigIntegerField(verbose_name='قیمت محصول'),
        ),
    ]
