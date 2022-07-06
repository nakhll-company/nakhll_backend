from django.db import models
from functools import lru_cache


class AddressManager(models.Manager):
    pass


class ShopLogisticUnitManager(models.Manager):

    @lru_cache
    def __get_models(self):
        from logistic.models import (
            LogisticUnitGeneralSetting,
            ShopLogisticUnitConstraint,
            ShopLogisticUnitCalculationMetric
        )
        return (
            LogisticUnitGeneralSetting,
            ShopLogisticUnitConstraint,
            ShopLogisticUnitCalculationMetric
        )

    def generate_shop_logistic_units(self, shop):
        '''generate shop default logistic units'''
        default_logistic_units = self.get_default_logistic_units()
        for logistic_unit in default_logistic_units:
            self.generate_shop_logistic_unit(shop, logistic_unit)

    def get_default_logistic_units(self):
        '''get default logistic units defined by logistic team'''
        LogisticUnitGeneralSetting, _, _ = self.__get_models()
        return LogisticUnitGeneralSetting.objects.all()

    def generate_shop_logistic_unit(self, shop, logistic_unit):
        '''generate shop one logistic unit for shop'''
        _, ShopLogisticUnitConstraint, ShopLogisticUnitCalculationMetric = self.__get_models()
        shop_logistic_unit = self.create(
            shop=shop,
            name=logistic_unit.get_name_display(),
            is_active=logistic_unit.is_active,
            logo_type=logistic_unit.name)
        constraints = ShopLogisticUnitConstraint.objects.create(
            shop_logistic_unit=shop_logistic_unit,
        )
        if logistic_unit.is_only_for_shop_city and shop.City:
            constraints.cities.add(shop.City)
        ShopLogisticUnitCalculationMetric.objects.create(
            shop_logistic_unit=shop_logistic_unit,
            price_per_kilogram=logistic_unit.default_price_per_kilogram,
            price_per_extra_kilogram=logistic_unit.default_price_per_extra_kilogram,
        )
