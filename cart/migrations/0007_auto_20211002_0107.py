# Generated by Django 3.1.6 on 2021-10-01 21:37

import django.core.serializers.json
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0006_cartitem_extra_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cartitem',
            name='product_last_state',
            field=models.JSONField(encoder=django.core.serializers.json.DjangoJSONEncoder, null=True),
        ),
    ]