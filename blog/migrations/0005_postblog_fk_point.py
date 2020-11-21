# Generated by Django 2.2.6 on 2020-03-02 17:35

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('blog', '0004_commentpost'),
    ]

    operations = [
        migrations.AddField(
            model_name='postblog',
            name='FK_Point',
            field=models.ManyToManyField(blank=True, related_name='Post_Point', to=settings.AUTH_USER_MODEL, verbose_name='امتیاز دهنده'),
        ),
    ]
