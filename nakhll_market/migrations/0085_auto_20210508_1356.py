# Generated by Django 3.1.6 on 2021-05-08 09:26

from django.db import migrations, models
import django.db.models.deletion
import django_jalali.db.models

from Iran import data
from nakhll_market.models import State, BigCity, City

def fill_iran_data(apps, schema_editor):
    states = list(filter(lambda i: i['divisionType']==1, data))
    big_cities = list(filter(lambda i: i['divisionType']==2, data))
    cities = list(filter(lambda i: i['divisionType']==3, data))
    for state in states:
        State.objects.create(id=state['id'] ,name=state['name'], code=int(state['code']))
    for big_city in big_cities:
        state = State.objects.get(id=big_city['parentCountryDivisionId'])
        BigCity.objects.create(id=big_city['id'], name=big_city['name'], code=int(big_city['code']), state=state)
    for city in cities:
        big_city = BigCity.objects.get(id=city['parentCountryDivisionId'])
        City.objects.create(id=city['id'], name=city['name'], code=int(city['code']), big_city=big_city)




class Migration(migrations.Migration):

    dependencies = [
        ('nakhll_market', '0084_auto_20210307_1954'),
    ]

    operations = [
        migrations.CreateModel(
            name='BigCity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=127, verbose_name='نام شهرستان')),
                ('code', models.IntegerField(verbose_name='شهرستان')),
            ],
            options={
                'verbose_name': 'شهرستان',
                'verbose_name_plural': 'شهرستان ها',
                'ordering': ('id',),
            },
        ),
        migrations.CreateModel(
            name='State',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=127, verbose_name='نام استان')),
                ('code', models.IntegerField(verbose_name='استان')),
            ],
            options={
                'verbose_name': 'استان',
                'verbose_name_plural': 'استان ها',
                'ordering': ('id',),
            },
        ),
        migrations.AlterField(
            model_name='profile',
            name='BrithDay',
            field=django_jalali.db.models.jDateField(null=True, verbose_name='تاریخ تولد'),
        ),
        migrations.CreateModel(
            name='City',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=127, verbose_name='نام شهر')),
                ('code', models.IntegerField(verbose_name='شهر')),
                ('big_city', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='city', to='nakhll_market.bigcity')),
            ],
            options={
                'verbose_name': 'شهر',
                'verbose_name_plural': 'شهر ها',
                'ordering': ('id',),
            },
        ),
        migrations.AddField(
            model_name='bigcity',
            name='state',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='big_city', to='nakhll_market.state'),
        ),
        migrations.RunPython(fill_iran_data, migrations.RunPython.noop)
    ]
