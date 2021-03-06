# Generated by Django 3.1.6 on 2021-12-16 06:50

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('nakhll_market', '0135_auto_20211205_1607'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('logistic', '0005_address_old_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='LogisticUnit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='نام  ')),
                ('description', models.TextField(blank=True, null=True, verbose_name='توضیحات')),
                ('is_publish', models.BooleanField(default=True, verbose_name='منتشر شده؟')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='ایجاد کننده')),
            ],
            options={
                'verbose_name': 'واحد ارسال',
                'verbose_name_plural': 'واحد ارسال',
            },
        ),
        migrations.CreateModel(
            name='LogisticUnitConstraintParameter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('min_price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='حداقل قیمت')),
                ('max_weight_g', models.PositiveIntegerField(verbose_name='حداکثر وزن (گرم)')),
                ('max_package_value', models.PositiveIntegerField(verbose_name='حداکثر ارزش بسته')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')),
                ('cities', models.ManyToManyField(to='nakhll_market.City', verbose_name='شهرها')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='ایجاد کننده')),
                ('products', models.ManyToManyField(to='nakhll_market.Product', verbose_name='محصولات')),
            ],
            options={
                'verbose_name': 'پارامتر محدودیت ارسال',
                'verbose_name_plural': 'پارامتر محدودیت ارسال',
            },
        ),
        migrations.CreateModel(
            name='LogisticUnitMetric',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price_per_kg', models.PositiveIntegerField(verbose_name='قیمت هر کیلوگرم')),
                ('price_per_extra_kg', models.PositiveIntegerField(verbose_name='قیمت هر کیلوگرم اضافه')),
                ('is_default', models.BooleanField(default=False, verbose_name='پیش فرض؟')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='ایجاد کننده')),
            ],
            options={
                'verbose_name': 'متریک ارسال',
                'verbose_name_plural': 'متریک ارسال',
            },
        ),
        migrations.CreateModel(
            name='ShopLogisticUnit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=True, verbose_name='فعال؟')),
                ('use_default_setting', models.BooleanField(default=True, verbose_name='استفاده از تنظیم پیش فرض؟')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')),
                ('logistic_unit', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='logistic.logisticunit', verbose_name='واحد ارسال')),
                ('shop', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='nakhll_market.shop', verbose_name='فروشگاه')),
            ],
            options={
                'verbose_name': 'واحد ارسال فروشگاه',
                'verbose_name_plural': 'واحد ارسال فروشگاه',
            },
        ),
        migrations.CreateModel(
            name='ShopLogisticUnitMetric',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')),
                ('metric', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='logistic.logisticunitmetric', verbose_name='متریک')),
                ('shop_logistic_unit_constraint', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='logistic.shoplogisticunit', verbose_name='واحد ارسال فروشگاه')),
            ],
            options={
                'verbose_name': 'متریک فروشگاه',
                'verbose_name_plural': 'متریک فروشگاه',
            },
        ),
        migrations.CreateModel(
            name='ShopLogisticUnitConstraint',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=True, verbose_name='فعال؟')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')),
                ('constraint', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='logistic.logisticunitconstraintparameter', verbose_name='محدودیت')),
                ('shop_logistic_unit', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='logistic.shoplogisticunit', verbose_name='واحد ارسال فروشگاه')),
            ],
            options={
                'verbose_name': 'محدودیت ارسال فروشگاه',
                'verbose_name_plural': 'محدودیت ارسال فروشگاه',
            },
        ),
        migrations.CreateModel(
            name='LogisticUnitConstraint',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_publish', models.BooleanField(default=True, verbose_name='منتشر شده؟')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')),
                ('constraint', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='logistic.logisticunitconstraintparameter', verbose_name='محدودیت')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='ایجاد کننده')),
                ('logistic_unit', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='logistic.logisticunit', verbose_name='واحد ارسال')),
            ],
            options={
                'verbose_name': 'محدودیت ارسال',
                'verbose_name_plural': 'محدودیت ارسال',
            },
        ),
        migrations.AddField(
            model_name='logisticunit',
            name='metric',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='logistic.logisticunitmetric', verbose_name='متریک'),
        ),
    ]
