# Generated by Django 3.1.6 on 2021-11-01 11:10

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('nakhll_market', '0128_auto_20211101_1309'),
    ]

    operations = [
        migrations.RenameField(
            model_name='newcategory',
            old_name='is_active',
            new_name='available',
        ),
        migrations.AddField(
            model_name='newcategory',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='تاریخ ایجاد'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='newcategory',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی'),
        ),
    ]
