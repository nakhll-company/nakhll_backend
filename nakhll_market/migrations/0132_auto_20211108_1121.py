# Generated by Django 3.1.6 on 2021-11-08 07:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nakhll_market', '0131_newcategory_order'),
    ]

    operations = [
        migrations.AlterField(
            model_name='newcategory',
            name='order',
            field=models.PositiveIntegerField(default=99999, verbose_name='ترتیب'),
        ),
    ]