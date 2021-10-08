# Generated by Django 3.1.6 on 2021-08-15 08:48

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('nakhll_market', '0106_auto_20210806_1748'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address', models.TextField(verbose_name='آدرس')),
                ('zip_code', models.CharField(max_length=10, verbose_name='کد پستی')),
                ('phone_number', models.CharField(max_length=11, verbose_name='تلفن ثابت')),
                ('big_city', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='addresses', to='nakhll_market.bigcity', verbose_name='شهرستان')),
                ('city', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='addresses', to='nakhll_market.city', verbose_name='شهر')),
                ('state', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='addresses', to='nakhll_market.state', verbose_name='استان')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='addresses', to=settings.AUTH_USER_MODEL, verbose_name='کاربر')),
            ],
            options={
                'verbose_name': 'آدرس',
                'verbose_name_plural': 'آدرس\u200cها',
            },
        ),
    ]
