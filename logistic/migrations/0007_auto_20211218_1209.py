# Generated by Django 3.1.6 on 2021-12-18 08:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('nakhll_market', '0135_auto_20211205_1607'),
        ('logistic', '0006_auto_20211216_1020'),
    ]

    operations = [
        migrations.AddField(
            model_name='logisticunitconstraintparameter',
            name='categories',
            field=models.ManyToManyField(to='nakhll_market.NewCategory', verbose_name='دسته بندی ها'),
        ),
        migrations.AlterField(
            model_name='shoplogisticunitconstraint',
            name='constraint',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='shop_logistic_unit_constraint', to='logistic.logisticunitconstraintparameter', verbose_name='محدودیت'),
        ),
        migrations.AlterField(
            model_name='shoplogisticunitmetric',
            name='metric',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, to='logistic.logisticunitmetric', verbose_name='متریک'),
        ),
        migrations.AlterField(
            model_name='shoplogisticunitmetric',
            name='shop_logistic_unit_constraint',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='shop_logistic_unit_metric', to='logistic.shoplogisticunitconstraint', verbose_name='واحد ارسال فروشگاه'),
        ),
    ]
