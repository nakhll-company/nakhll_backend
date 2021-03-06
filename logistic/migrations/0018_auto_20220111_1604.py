# Generated by Django 3.1.6 on 2022-01-11 12:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logistic', '0017_auto_20220105_1031'),
    ]

    operations = [
        migrations.AddField(
            model_name='shoplogisticunitcalculationmetric',
            name='pay_time',
            field=models.CharField(choices=[('when_buying', 'هنگام خرید'), ('at_delivery', 'هنگام تحویل')], default='when_buying', max_length=11, verbose_name='زمان پرداخت'),
        ),
        migrations.AddField(
            model_name='shoplogisticunitcalculationmetric',
            name='payer',
            field=models.CharField(choices=[('shop', 'فروشگاه'), ('cust', 'مشتری')], default='cust', max_length=4, verbose_name='پرداخت کننده'),
        ),
    ]
