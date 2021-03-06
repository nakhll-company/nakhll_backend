# Generated by Django 2.2.6 on 2021-01-01 11:48

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SMS',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('return_status', models.IntegerField()),
                ('return_message', models.CharField(max_length=50, verbose_name='پیام درخواست')),
                ('entries_cost', models.IntegerField(verbose_name='مبلغ')),
                ('entries_datetime', models.DateTimeField()),
                ('entries_receptor', models.CharField(max_length=50)),
                ('entries_sender', models.CharField(max_length=50)),
                ('entries_statustext', models.CharField(max_length=50)),
                ('entries_status', models.IntegerField()),
                ('entries_message', models.CharField(max_length=255)),
                ('entries_messageid', models.IntegerField()),
                ('datetime', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'پیامک',
                'verbose_name_plural': 'پیامک ها',
                'ordering': ('-entries_datetime',),
            },
        ),
    ]
