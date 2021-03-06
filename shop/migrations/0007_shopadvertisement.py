# Generated by Django 3.1.6 on 2022-01-04 09:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('nakhll_market', '0135_auto_20211205_1607'),
        ('shop', '0006_auto_20211107_1735'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShopAdvertisement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('yektanet_id', models.CharField(blank=True, max_length=20, null=True, verbose_name='شناسه تبلیغاتی یکتانت')),
                ('yektanet_status', models.IntegerField(choices=[(1, 'فعال'), (0, 'غیرفعال')], default=1, verbose_name='وضعیت تبلیغاتی یکتانت')),
                ('shop', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='advertisement', to='nakhll_market.shop', verbose_name='حجره')),
            ],
            options={
                'verbose_name': 'تبلیغات',
                'verbose_name_plural': 'تبلیغات',
                'ordering': ('-id',),
            },
        ),
    ]
