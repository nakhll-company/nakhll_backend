from django.db.models.expressions import Case, Value, When
from django.db.models import fields
from django.utils.translation import ugettext as _
from rest_framework import serializers
from logistic.models import Address, ShopLogisticUnit, ShopLogisticUnitConstraint, ShopLogisticUnitCalculationMetric
from nakhll_market.models import Product, Shop, State, BigCity, City
from nakhll_market.serializer_fields import Base64ImageField
from restapi.serializers import BigCitySerializer, CitySerializer, StateSerializer
from nakhll_market.mixins import DriveBigCityAndStateFromCityMixin

class AddressReadSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    state = StateSerializer(many=False, read_only=True)
    big_city = BigCitySerializer(many=False, read_only=True)
    city = CitySerializer(many=False, read_only=True)

    class Meta:
        model = Address
        fields = (
            'id',
            'user',
            'city',
            'state',
            'big_city',
            'zip_code',
            'address',
            'phone_number',
            'receiver_full_name',
            'receiver_mobile_number',
        )
        read_only_fields = ('id', 'user',)

    def get_user(self, obj):
        return obj.user.first_name + ' ' + obj.user.last_name


class AddressWriteSerializer(
        DriveBigCityAndStateFromCityMixin,
        serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = (
            'id',
            'city',
            'zip_code',
            'address',
            'phone_number',
            'receiver_full_name',
            'receiver_mobile_number',
        )
        read_only_fields = ('id',)


class ShopOwnerAddressReadSerializer(AddressReadSerializer):
    class Meta:
        model = Address
        fields = ('id', 'user', 'state', 'big_city', 'city', 'zip_code',
                  'address', 'receiver_full_name', 'receiver_mobile_number',)
        read_only_fields = ('id', 'user')


class ProductSerializer(serializers.ModelSerializer):
    is_checked = serializers.SerializerMethodField()
    class Meta:
        model = Product
        fields = ('ID', 'Title', 'is_checked')

    def get_is_checked(self, obj):
        return obj.is_checked



class ShopLogisticUnitSerializer(serializers.ModelSerializer):
    shop = serializers.SlugRelatedField(slug_field='Slug', queryset=Shop.objects.all())
    constraint_id = serializers.SerializerMethodField()
    metric_id = serializers.SerializerMethodField()
    cities_count = serializers.SerializerMethodField()
    products_count = serializers.SerializerMethodField()
    logo = Base64ImageField(max_length=None, use_url=True, allow_empty_file=False, required=False)
    class Meta:
        model = ShopLogisticUnit
        fields = ('id', 'shop', 'name', 'description', 'logo', 'is_active', 'is_publish',
                  'constraint_id', 'metric_id', 'cities_count', 'products_count', )
        read_only_fields = ('id', 'is_publish', )

    def get_constraint_id(self, obj):
        return obj.constraint.id if hasattr(obj, 'constraint') else None
    
    def get_metric_id(self, obj):
        return obj.calculation_metric.id if hasattr(obj, 'calculation_metric') else None

    def get_cities_count(self, obj):
        if not obj.constraint or not obj.constraint.cities:
            return 0
        return obj.constraint.cities.count()

    def get_products_count(self, obj):
        if not obj.constraint or not obj.constraint.products:
            return 0
        return obj.constraint.products.count()

        

class ShopLogisticUnitConstraintReadSerializer(serializers.ModelSerializer):
    shop_logistic_unit = serializers.PrimaryKeyRelatedField(read_only=True)
    products = serializers.SerializerMethodField()
    class Meta:
        model = ShopLogisticUnitConstraint
        fields = ('id', 'shop_logistic_unit', 'cities', 'products', 'categories', 'max_weight', 'min_weight', 
                  'max_cart_price', 'min_cart_price', 'max_cart_count', 'min_cart_count', )
        read_only_fields = ('id', 'shop_logistic_unit', )
    
    def get_products(self, obj):
        shop = obj.shop_logistic_unit.shop
        products = Product.objects.filter(
            FK_Shop=shop).annotate(is_checked=Case(
                When(ID__in=obj.products.values('ID'), then=Value(True)),
                default=Value(False),
                output_field=fields.BooleanField()
            )).order_by('-is_checked')
        return ProductSerializer(products, many=True).data
        

class ShopLogisticUnitConstraintWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopLogisticUnitConstraint
        fields = ('id', 'cities', 'products', 'categories', 'max_weight', 'min_weight', 
                  'max_cart_price', 'min_cart_price', 'max_cart_count', 'min_cart_count', )
        read_only_fields = ('id', )

    def validate_products(self, products):
        if not self._are_products_belong_to_shop(products):
            raise serializers.ValidationError(_('این محصولات متعلق به فروشگاه شما نیستند.'))
        return products

    def _are_products_belong_to_shop(self, products):
        if not products:
            return True
        shop_products = self.instance.shop_logistic_unit.shop.ShopProduct.all()
        return set(products).issubset(set(shop_products))


class ShopLogisticUnitCalculationMetricSerializer(serializers.ModelSerializer):
    shop_logistic_unit = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = ShopLogisticUnitCalculationMetric
        fields = ('id', 'shop_logistic_unit', 'price_per_kilogram',
                  'price_per_extra_kilogram', 'payer', 'pay_time', )
        read_only_fields = ('id', 'shop_logistic_unit', )


class ShopLogisticUnitConstraintWithoutM2MSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopLogisticUnitConstraint
        fields = ('id', 'max_weight', 'min_weight', 'max_cart_price',
                  'min_cart_price', 'max_cart_count', 'min_cart_count', )
        read_only_fields = ('id', )



class ShopLogisticUnitFullSerializer(serializers.ModelSerializer):
    shop = serializers.SlugRelatedField(slug_field='Slug', queryset=Shop.objects.all())
    constraint = ShopLogisticUnitConstraintWithoutM2MSerializer(read_only=False, required=False)
    calculation_metric = ShopLogisticUnitCalculationMetricSerializer(read_only=False, required=False)
    cities_count = serializers.SerializerMethodField()
    products_count = serializers.SerializerMethodField()
    logo = Base64ImageField(max_length=None, use_url=True, allow_empty_file=False, required=False)
    class Meta:
        model = ShopLogisticUnit
        fields = ('id', 'shop', 'name', 'description', 'logo', 'logo_type', 'is_active', 'is_publish',
                  'constraint', 'calculation_metric', 'cities_count', 'products_count', )
        read_only_fields = ('id', 'is_publish', )

    def get_constraint_id(self, obj):
        return obj.constraint.id if hasattr(obj, 'constraint') else None
    
    def get_metric_id(self, obj):
        return obj.calculation_metric.id if hasattr(obj, 'calculation_metric') else None

    def get_cities_count(self, obj):
        if not obj.constraint or not obj.constraint.cities:
            return 0
        return obj.constraint.cities.count()

    def get_products_count(self, obj):
        if not obj.constraint or not obj.constraint.products:
            return 0
        return obj.constraint.products.count()

 
    def update(self, instance, validated_data):
        constraint_dict = validated_data.pop('constraint', {})
        metric_dict = validated_data.pop('calculation_metric', {})
        instance = super().update(instance, validated_data)

        constraint = instance.constraint
        for key, value in constraint_dict.items():
            setattr(constraint, key, value)
        constraint.save()

        metric = instance.calculation_metric
        for key, value in metric_dict.items():
            setattr(metric, key, value)
        metric.save()

        return instance


