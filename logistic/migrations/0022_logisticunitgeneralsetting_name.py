# Generated by Django 3.2.12 on 2022-06-07 16:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logistic', '0021_delete_postpricesetting'),
    ]

    operations = [
        migrations.AddField(
            model_name='logisticunitgeneralsetting',
            name='name',
            field=models.IntegerField(choices=[(0, 'پست پیشتاز'), (1, 'پست سفارشی')], default=0, verbose_name='نوع ارسال پستی'),
        ),
    ]
