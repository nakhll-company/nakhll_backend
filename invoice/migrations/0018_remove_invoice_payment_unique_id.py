# Generated by Django 3.1.6 on 2021-10-03 22:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('invoice', '0017_auto_20211004_0044'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='invoice',
            name='payment_unique_id',
        ),
    ]
