# Generated by Django 3.1.6 on 2021-12-21 08:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('logistic', '0005_address_old_id'),
        ('invoice', '0025_auto_20211018_1423'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoice',
            name='address',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='invoices', to='logistic.address', verbose_name='آدرس'),
        ),
    ]
