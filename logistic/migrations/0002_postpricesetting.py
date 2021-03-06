# Generated by Django 3.1.6 on 2021-08-15 12:40

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import logistic.interfaces


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('logistic', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PostPriceSetting',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('inside_city_price', models.PositiveIntegerField(default=150000, verbose_name='قیمت پست درون شهری (ریال)')),
                ('outside_city_price', models.PositiveIntegerField(default=200000, verbose_name='قیمت پست برون شهری (ریال)')),
                ('extra_weight_fee', models.PositiveIntegerField(default=20000, verbose_name='قیمت به ازای هر کیلو اضافه (ریال)')),
                ('created_datetime', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('updated_datetime', models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='post_price_settings', to=settings.AUTH_USER_MODEL, verbose_name='کاربر')),
            ],
            options={
                'verbose_name': 'تنظیمات قیمت پستی',
                'verbose_name_plural': 'تنظیمات قیمت پستی',
            },
        ),
    ]
