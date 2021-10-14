# Generated by Django 3.1.6 on 2021-07-15 10:21

import Payment.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('Payment', '0063_auto_20210708_1332'),
    ]

    operations = [
        migrations.CreateModel(
            name='DashboardBanner',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to=Payment.models.PathAndRename('media/Pictures/Dashboard/Banner/'), verbose_name='عکس بنر')),
                ('url', models.URLField(max_length=100, null=True, verbose_name='لینک بنر')),
                ('created_datetime', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ثبت')),
                ('publish_status', models.CharField(choices=[('pub', 'منتشر شده'), ('prv', 'پیش\u200cنمایش')], default='pub', max_length=3)),
                ('staff_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='dashboard_banners', to=settings.AUTH_USER_MODEL, verbose_name='کارشناس')),
            ],
            options={
                'verbose_name': 'بنر داشبرد',
                'verbose_name_plural': 'بنرهای داشبرد',
            },
        ),
    ]
