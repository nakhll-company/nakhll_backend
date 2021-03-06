# Generated by Django 3.1.6 on 2022-05-01 14:36

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def create_dummy_user(apps, schema_editor):
    User = apps.get_model("auth", "User")
    dummy_user = User.objects.create(
        username="dummy",
        is_active=False,
    )


def create_dummy_shop(apps, schema_editor):
    Shop = apps.get_model("nakhll_market", "Shop")
    User = apps.get_model("auth", "User")
    dummy_user = User.objects.get(username="dummy")
    dumm_shop = Shop.objects.create(
        Title = "dummy",
        FK_ShopManager = dummy_user,
        Slug = "dummy",
    )


def assign_product_without_shop_and_manager_to_dummy(apps, schema_editor):
    User = apps.get_model("auth", "User")
    Shop = apps.get_model("nakhll_market", "Shop")
    Product = apps.get_model("nakhll_market", "Product")
    dummy_user = User.objects.get(username="dummy")
    dummy_shop = Shop.objects.get(Title="dummy")
    products_without_shop = Product.objects.filter(FK_Shop=None)
    for product in products_without_shop:
        product.FK_Shop = dummy_shop
        product.save()


def assign_shop_without_manager(apps, schema_editor):
    User = apps.get_model("auth", "User")
    Shop = apps.get_model("nakhll_market", "Shop")
    dummy_user = User.objects.get(username="dummy")
    shops_without_manager = Shop.objects.filter(FK_ShopManager=None)
    for shop in shops_without_manager:
        shop.FK_ShopManager = dummy_user
        shop.save()


def duplicate_shop_title(apps, schema_editor):
    Shop = apps.get_model("nakhll_market", "Shop")
    titles = list(Shop.objects.values_list("Title", flat=True))
    duplicated_titles = set(filter(lambda title: titles.count(title) > 1, titles))
    for title in duplicated_titles:
        shops = Shop.objects.filter(Title=title)
        for num, shop in enumerate(shops):
            shop.Title = f"{title}_duplicate_{num}"
            shop.Available = False
            shop.Publish = False
            shop.save()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('nakhll_market', '0144_tag'),
    ]

    operations = [
        migrations.RunPython(create_dummy_user, migrations.RunPython.noop),
        migrations.RunPython(create_dummy_shop, migrations.RunPython.noop),
        migrations.RunPython(assign_product_without_shop_and_manager_to_dummy, migrations.RunPython.noop),
        migrations.RunPython(assign_shop_without_manager, migrations.RunPython.noop),
        migrations.RunPython(duplicate_shop_title, migrations.RunPython.noop),
    ]
