# Generated by Django 3.1.6 on 2021-10-01 21:16

import django.core.serializers.json
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0005_auto_20211001_2352'),
    ]

    operations = [
        migrations.AddField(
            model_name='cartitem',
            name='extra_data',
            field=models.JSONField(encoder=django.core.serializers.json.DjangoJSONEncoder, null=True),
        ),
    ]
