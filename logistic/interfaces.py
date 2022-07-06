from django.db.models.aggregates import Sum
from django.db.models.functions import Cast
from django.db.models.fields import FloatField
from django.db.models.query import QuerySet
from django.db.models.query_utils import Q
from django.db.models import F
from django.utils.translation import ugettext as _
from rest_framework.validators import ValidationError
from nakhll_market.models import Product, Shop
from logistic.exceptions import NoLogisticUnitAvailableException


class LogisticUnitInterface:
    def __init__(self, cart) -> None:
        self.total_price = 0
        self.cart = cart
        self.logistic_units = []
        self.errors = []

    # TODO: chagne create to generate
    # TODO: remove return statement as it save items to self
    def generate_logistic_unit_list(self):
        for shop in self.cart.shops:
            shop_obj = ShopLogisticUnitInterface(self.cart, shop)
            shop_obj.generate_shop_logistic_units()

            self.errors.extend(shop_obj.errors)
            self.total_price += shop_obj.total_price
            self.logistic_units.append(shop_obj.logistic_units)

        if self.errors:
            self.cart.items.filter(product__in=self.errors).delete()
            raise ValidationError(_('این محصولات هیچ روش ارسالی ندارند و از سبد خرید شما حذف خواهند شد<br>{}').format(
                '<br>'.join([product.Title for product in self.errors])
            ))

        # TODO: after fixing purchase process
        # if no_item:
        #     raise ValidationError({
        #         'errors': [_('No Item to purchase')],
        #         'redirect': 'https://nakhll.com/cart/'
        #         })

    def as_dict(self):
        return {
            "errors": self.errors,
            "total_price": self.total_price,
            "logistic_units": self.logistic_units,
        }


class ShopLogisticUnitInterface:
    PAD_UNIT_TYPE = 'pad'
    FREE_UNIT_TYPE = 'free'

    def __init__(self, cart, shop):
        self.total_price = 0
        self.cart = cart
        self.shop = shop
        self.__logistic_units = []
        self.errors = []
        self.available_logistic_units = self.get_available_logistic_units(shop)
        self.all_products = self.cart.products.filter(FK_Shop=self.shop)
        self.pad_products = self.pop_only_pad_products()
        self.free_products = self.pop_free_products()
        self.total_weight = self.get_total_weight()

    def generate_shop_logistic_units(self):
        products_available_units = []

        if self.pad_products:
            pad_lu_name = self._get_pad_lu_name()
            self.__logistic_units.append({
                'unit_name': pad_lu_name,
                'unit_type': self.PAD_UNIT_TYPE,
                'products': [
                    {'slug': product.slug, 'title': product.Title, 'image': product.image_thumbnail_url}
                    for product in self.pad_products
                ],
                'price': 0
            })

        if self.free_products:
            free_lu_name = self._get_free_lu_name()
            self.__logistic_units.append({
                'unit_name': free_lu_name,
                'unit_type': self.FREE_UNIT_TYPE,
                'products': [
                    {'slug': product.slug, 'title': product.Title, 'image': product.image_thumbnail_url}
                    for product in self.free_products
                ],
                'price': 0
            })

        if self.all_products:
            all_products_set = set()
            for product in self.all_products:
                product_available_lus = self.get_product_available_logistic_units(product, exclude_pads=True)
                if not product_available_lus:
                    self.errors.append(product)
                    self.cart.items.filter(product=product).delete()
                else:
                    all_products_set.add(product)
                    products_available_units.append(set(product_available_lus))

            if not products_available_units or not set.intersection(*products_available_units):
                raise NoLogisticUnitAvailableException()
            joint_units = set.intersection(*products_available_units)

            optimal_unit, self.total_price = self.get_optimal_unit_and_price(joint_units)
            products = [{'slug': product.slug, 'title': product.Title, 'image': product.image_thumbnail_url}
                        for product in all_products_set]

            self.__logistic_units.append({
                'unit_name': optimal_unit.name,
                'unit_type': '',
                'products': products,
                'price': self.total_price
            })

    @property
    def logistic_units(self):
        return {
            'price': self.total_price,
            'errors': self.errors,
            'shop_name': self.shop.Title,
            'shop_slug': self.shop.Slug,
            'logistic_units': self.__logistic_units
        }

    def get_total_weight(self):
        return self.cart.items.filter(product__FK_Shop=self.shop).aggregate(
            total_weight=Sum(Cast(Cast(
                'product__Weight_With_Packing',
                output_field=FloatField()
            ) * F('count'), output_field=FloatField()))
        )['total_weight']

    def pop_only_pad_products(self):
        only_pad_ids = []
        for product in self.all_products:
            all_lus = self.get_product_available_logistic_units(product)
            pad_lus = self.get_pad_lus()
            if set(all_lus) == set(pad_lus) and len(all_lus) != 0:
                only_pad_ids.append(product.ID)
        only_pad_products = Product.objects.filter(ID__in=only_pad_ids)
        self.all_products = self.all_products.difference(only_pad_products)
        return only_pad_products

    def pop_free_products(self):
        free_products_qs = self.get_free_lus()
        free_products = Product.objects.filter(
            ID__in=free_products_qs.values_list('constraint__products__ID', flat=True))
        self.all_products = self.all_products.difference(free_products)
        return free_products

    def _get_pad_lu_name(self):
        lu = self.get_pad_lus().first()
        if lu:
            return lu.name
        return 'پسکرایه'

    def _get_free_lu_name(self):
        lu = self.get_free_lus().first()
        if lu:
            return lu.name
        return 'ارسال رایگان'

    def shop_active_logistic_units(self, shop):
        return models.ShopLogisticUnit.objects.filter(
            shop=shop, is_active=True)

    def get_available_logistic_units(self, shop):
        queryset = self.shop_active_logistic_units(shop)
        sum_shop_cart_price = self.cart.products.filter(FK_Shop=shop).aggregate(
            total_price=Sum('Price')
        )['total_price']
        filter_queryset = Q(
            Q(constraint__cities=self.cart.address.city) |
            Q(constraint__cities=None)
        )
        filter_queryset &= Q(constraint__min_cart_price__lte=sum_shop_cart_price)
        return queryset.filter(filter_queryset)

    def get_product_available_logistic_units(self, product: Product, *, exclude_pads=False):
        filter_queryset = Q()
        filter_queryset &= Q(
            Q(constraint__products=product) |
            Q(constraint__products=None)
        )
        # TODO: max weight should be calculated base on all products, not just one
        weight = int(product.Weight_With_Packing) / 1000
        filter_queryset &= Q(
            Q(constraint__max_weight__gte=weight) |
            Q(constraint__max_weight=0)
        )
        queryset = self.available_logistic_units.filter(filter_queryset)
        if exclude_pads:
            pad_filter_queryset = Q(
                calculation_metric__pay_time=models.ShopLogisticUnitCalculationMetric.PayTimes.AT_DELIVERY)
            pad_filter_queryset &= Q(
                calculation_metric__payer=models.ShopLogisticUnitCalculationMetric.PayerTypes.CUSTOMER)
            queryset = queryset.exclude(pad_filter_queryset)

        return queryset

    def get_optimal_unit_and_price(self, units):
        minimum_price = None
        optimal_unit = None
        for unit in units:
            price = self.calculate_logistic_price(unit)
            if minimum_price is None or price < minimum_price:
                minimum_price = price
                optimal_unit = unit
        return optimal_unit, minimum_price

    def calculate_logistic_price(self, unit):
        extra_weight = int((self.total_weight + 1) / 1000)
        price = unit.calculation_metric.price_per_kilogram
        price += unit.calculation_metric.price_per_extra_kilogram * extra_weight
        return price

    def get_pad_lus(self):
        filter_queryset = Q(calculation_metric__pay_time=models.ShopLogisticUnitCalculationMetric.PayTimes.AT_DELIVERY)
        filter_queryset &= Q(calculation_metric__payer=models.ShopLogisticUnitCalculationMetric.PayerTypes.CUSTOMER)
        return self.available_logistic_units.filter(filter_queryset)

    def get_free_lus(self):
        filter_queryset = Q(calculation_metric__pay_time=models.ShopLogisticUnitCalculationMetric.PayTimes.WHEN_BUYING)
        filter_queryset &= Q(calculation_metric__payer=models.ShopLogisticUnitCalculationMetric.PayerTypes.SHOP)
        return self.available_logistic_units.filter(filter_queryset)


def generate_shop_logistic_units():
    SLU = models.ShopLogisticUnit
    for shop in Shop.objects.all():
        SLU.objects.generate_logistic_units(shop)


from logistic import models
