# Generated by Django 3.1.6 on 2021-12-27 05:38

import django.core.serializers.json
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoice', '0025_auto_20211018_1423'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='logistic_unit_details',
            field=models.JSONField(blank=True, encoder=django.core.serializers.json.DjangoJSONEncoder, null=True, verbose_name='جزئیات واحد حمل و نقل'),
        ),
    ]
