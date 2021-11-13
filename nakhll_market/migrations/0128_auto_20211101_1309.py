# Generated by Django 3.1.6 on 2021-11-01 09:39

from django.db import migrations, models
import django.db.models.deletion
import nakhll_market.models


class Migration(migrations.Migration):

    dependencies = [
        ('nakhll_market', '0127_historicalproduct'),
    ]

    operations = [
        migrations.CreateModel(
            name='NewCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, verbose_name='عنوان دسته بندی')),
                ('slug', models.SlugField(unique=True, verbose_name='شناسه دسته بندی')),
                ('description', models.TextField(blank=True, verbose_name='درباره دسته بندی')),
                ('image', models.ImageField(blank=True, help_text='عکس دسته بندی را اینجا وارد کنید', null=True, upload_to=nakhll_market.models.PathAndRename('media/Pictures/Categories/'), verbose_name='عکس دسته بندی')),
                ('is_active', models.BooleanField(default=True, verbose_name='فعال')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='childrens', to='nakhll_market.newcategory', verbose_name='پدر')),
            ],
            options={
                'verbose_name': 'دسته بندی',
                'verbose_name_plural': 'دسته بندی ها',
            },
        ),
        migrations.AddField(
            model_name='historicalproduct',
            name='new_category',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='nakhll_market.newcategory', verbose_name='دسته بندی جدید'),
        ),
        migrations.AddField(
            model_name='product',
            name='new_category',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='products', to='nakhll_market.newcategory', verbose_name='دسته بندی جدید'),
        ),
    ]