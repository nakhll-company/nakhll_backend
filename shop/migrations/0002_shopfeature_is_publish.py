# Generated by Django 3.1.6 on 2021-11-07 06:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='shopfeature',
            name='is_publish',
            field=models.BooleanField(default=True, verbose_name='منتشر شده؟'),
        ),
    ]
