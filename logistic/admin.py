from django.contrib import admin
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from logistic.models import (LogisticUnitGeneralSetting, ShopLogisticUnit,
                             ShopLogisticUnitCalculationMetric,
                             ShopLogisticUnitConstraint)

# Register your models here.

admin.site.register(ShopLogisticUnit)
admin.site.register(ShopLogisticUnitConstraint)


@admin.register(ShopLogisticUnitCalculationMetric)
class ShopLogisticUnitCalculationMetricAdmin(admin.ModelAdmin):
    '''ShopLogisticUnitCalculationMetricAdmin'''
    actions = ['update_metrics_to_default']
    list_display = [
        'shop_logistic_unit',
        'shop_logistic_unit__name',
        'shop_logistic_unit__logo_type',
        'price_per_kilogram',
        'price_per_extra_kilogram']
    list_filter = ['shop_logistic_unit__name', 'shop_logistic_unit__logo_type']

    @admin.display(ordering='shop_logistic_unit__name',
                   description='نام واحد ارسال')
    def shop_logistic_unit__name(self, obj):
        return obj.shop_logistic_unit.name

    @admin.display(ordering='shop_logistic_unit__logo_type',
                   description='نوع لوگو')
    def shop_logistic_unit__logo_type(self, obj):
        return obj.shop_logistic_unit.get_logo_type_display()

    @admin.action(description='هزینه ارسال واحد های ارسال انتخاب شده را به مقدار پیشفرض بروز رسانی کن.')
    def update_metrics_to_default(self, request, queryset):
        ''' update shop logistic units metrics to default'''
        default_logistic_unit_metrics = LogisticUnitGeneralSetting.objects.all()
        counts = {}
        for metric in default_logistic_unit_metrics:
            counts[metric] = queryset.filter(
                # TODO Is shop_logistic_unit.name the parameter or logo_type?
                shop_logistic_unit__name=metric.get_name_display()).update(
                price_per_kilogram=metric.default_price_per_kilogram,
                price_per_extra_kilogram=metric.default_price_per_extra_kilogram)

        def generate_message(counts):
            message = ''
            for metric, count in counts.items():
                message += f'{count} متریک واحد لجستیکی از نوع {metric} بروز رسانی شد.'
            return message
        self.message_user(
            request,
            _(generate_message(counts)),
            messages.SUCCESS)


@admin.register(LogisticUnitGeneralSetting)
class LogisticUnitGeneralSettingAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'is_active',
        'default_price_per_kilogram',
        'default_price_per_extra_kilogram']
    readonly_fields = ('updated_by',)
    exclude = (
        'maximum_price_per_kilogram',
        'maximum_price_per_extra_kilogram',
    )

    def save_model(self, request, obj, form, change) -> None:
        obj.updated_by = request.user
        return super().save_model(request, obj, form, change)
