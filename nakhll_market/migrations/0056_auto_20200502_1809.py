# Generated by Django 2.2.6 on 2020-05-02 13:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nakhll_market', '0055_product_inventory'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user_view',
            name='User_Ip',
            field=models.CharField(blank=True, max_length=20, verbose_name='آدرس ای پی'),
        ),
    ]
