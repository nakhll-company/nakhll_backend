# Generated by Django 2.2.6 on 2019-12-26 19:57

import Ticketing.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Ticketing', '0008_complaint'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ticketing',
            name='Image',
            field=models.ImageField(blank=True, help_text='عکس مربوط به تیکت خود را اینجا بارگذاری کنید', null=True, upload_to=Ticketing.models.PathAndRename('media/Pictures/Ticketing/'), verbose_name='عکس تیکت'),
        ),
    ]
