# Generated by Django 3.2.12 on 2022-05-18 10:30

from django.db import migrations, models
import django.db.models.deletion


def cleanup_data(apps, schema_editor):
    '''shop state, big_city, city was embed, but they become dirty,
    so we want to make them referenced'''
    Shop = apps.get_model("nakhll_market", "Shop")
    State = apps.get_model("nakhll_market", "State")
    City = apps.get_model("nakhll_market", "City")
    BigCity = apps.get_model("nakhll_market", "BigCity")

    def find_it(model, name, **kwargs):
        try:
            return model.objects.get(name=name, **kwargs).pk
        except BaseException:
            try:
                return model.objects.get(id=name, **kwargs).pk
            except BaseException:
                return None

    for shop in Shop.objects.all():
        _state = shop.State
        _big_city = shop.BigCity
        _city = shop.City

        state = find_it(State, _state)
        if state:
            big_city = find_it(BigCity, _big_city, state=state)
        else:
            big_city = None
        if big_city:
            city = find_it(City, _city, big_city=big_city)
        else:
            city = None
        shop.State = state
        shop.BigCity = big_city
        shop.City = city
        shop.save()


class Migration(migrations.Migration):

    dependencies = [
        ('nakhll_market', '0147_auto_20220518_1459'),
    ]

    operations = [
        migrations.RunPython(cleanup_data, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='shop', name='BigCity', field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to='nakhll_market.bigcity', verbose_name='شهرستان'),),
        migrations.AlterField(
            model_name='shop', name='City', field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to='nakhll_market.city', verbose_name='شهر'),),
        migrations.AlterField(
            model_name='shop', name='State', field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to='nakhll_market.state', verbose_name='استان'),), ]
