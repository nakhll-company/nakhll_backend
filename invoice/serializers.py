from django.utils.timezone import localtime
import jdatetime
import json
from rest_framework import serializers
from .models import Invoice, InvoiceItem
from logistic.models import Address
from logistic.serializers import AddressReadSerializer, ShopOwnerAddressReadSerializer
from coupon.models import Coupon
from coupon.serializers import CouponUsageSerializer
from nakhll_market.serializers import UserSerializer


class InvoiceItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(read_only=True)
    added_date_jalali = serializers.SerializerMethodField()
    added_time_jalali = serializers.SerializerMethodField()
    buyer = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    image_thumbnail = serializers.SerializerMethodField()
    shop_slug = serializers.SerializerMethodField()

    class Meta:
        model = InvoiceItem
        fields = [
            'id',
            'product',
            'slug',
            'name',
            'count',
            'price_with_discount',
            'weight',
            'price_without_discount',
            'barcode',
            'image',
            'image_thumbnail',
            'shop_slug',
            'shop_name',
            'added_date_jalali',
            'added_time_jalali',
            'buyer',
            'status']

    def get_added_date_jalali(self, obj):
        jalali_datetime = jdatetime.datetime.fromgregorian(
            datetime=obj.added_datetime, locale='fa_IR')
        return jalali_datetime.strftime('%Y/%m/%d')

    def get_added_time_jalali(self, obj):
        jalali_datetime = jdatetime.datetime.fromgregorian(
            datetime=obj.added_datetime, locale='fa_IR')
        return jalali_datetime.strftime('%H:%M')

    def get_buyer(self, obj):
        return obj.invoice.user.get_full_name()

    def get_image(self, obj):
        if obj.product.image:
            return obj.product.image
        return 'https://nakhll.com/media/Pictures/default.jpg'

    def get_image_thumbnail(self, obj):
        if obj.product.image_thumbnail_url:
            return obj.product.image_thumbnail_url
        return 'https://nakhll.com/media/Pictures/default.jpg'

    def get_shop_slug(self, obj):
        return obj.product.shop.slug


class InvoiceWriteSerializer(serializers.ModelSerializer):
    address = serializers.PrimaryKeyRelatedField(
        queryset=Address.objects.all(), required=False)
    coupon = serializers.SlugRelatedField(
        slug_field='code',
        queryset=Coupon.objects.all(),
        required=False)

    class Meta:
        model = Invoice
        fields = (
            'address',
            'coupon',
        )


class InvoiceRetrieveSerializer(serializers.ModelSerializer):
    address = ShopOwnerAddressReadSerializer(many=False, read_only=True)
    coupon_usages = CouponUsageSerializer(read_only=True, many=True)
    user = UserSerializer(many=False, read_only=True)
    items = serializers.SerializerMethodField(method_name='get_invoie_items')
    receiver_mobile_number = serializers.SerializerMethodField()
    created_time_jalali = serializers.SerializerMethodField()
    created_date_jalali = serializers.SerializerMethodField()

    def get_receiver_mobile_number(self, obj):
        if obj.address_json:
            address = json.loads(obj.address_json)
            return address.get('receiver_mobile_number')
        return None

    def get_created_date_jalali(self, obj):
        jalali_datetime = jdatetime.datetime.fromgregorian(
            datetime=obj.created_datetime, locale='fa_IR')
        return jalali_datetime.strftime('%Y/%m/%d')

    def get_created_time_jalali(self, obj):
        time = obj.created_datetime
        time = localtime(obj.created_datetime)
        jalali_datetime = jdatetime.datetime.fromgregorian(
            datetime=time, locale='fa_IR')
        return jalali_datetime.strftime('%H:%M')

    def get_invoie_items(self, obj):
        items = obj.items.order_by('product__FK_Shop')
        return InvoiceItemSerializer(items, many=True, read_only=True).data

    class Meta:
        model = Invoice
        fields = (
            'id',
            'items',
            'address',
            'address_json',
            'user',
            'payment_unique_id',
            'status',
            # 'inoivce_type',
            'invoice_price_with_discount',
            'invoice_price_without_discount',
            'coupon_usages',
            'logistic_price',
            'logistic_errors',
            'final_price',
            'created_date_jalali',
            'created_time_jalali',
            'coupons_total_price',
            'payment_request_datetime',
            'receiver_mobile_number',
            'logistic_unit_details',
        )


class InvoiceProviderRetrieveSerializer(serializers.ModelSerializer):
    address = AddressReadSerializer(many=False, read_only=True)
    coupon_usages = CouponUsageSerializer(read_only=True, many=True)
    user = UserSerializer(many=False, read_only=True)
    items = serializers.SerializerMethodField(method_name='get_invoie_items')
    receiver_mobile_number = serializers.SerializerMethodField()
    created_time_jalali = serializers.SerializerMethodField()
    created_date_jalali = serializers.SerializerMethodField()
    final_price = serializers.SerializerMethodField()
    invoice_price_with_discount = serializers.SerializerMethodField()
    invoice_price_without_discount = serializers.SerializerMethodField()

    def get_final_price(self, obj):
        user = self.context.get('request').user
        total = 0
        for item in obj.items.filter(product__FK_Shop__FK_ShopManager=user):
            price = item.product.Price
            total += price
        return total

    def get_receiver_mobile_number(self, obj):
        if obj.address_json:
            address = json.loads(obj.address_json)
            return address.get('receiver_mobile_number')
        return None

    def get_created_date_jalali(self, obj):
        jalali_datetime = jdatetime.datetime.fromgregorian(
            datetime=obj.created_datetime, locale='fa_IR')
        return jalali_datetime.strftime('%Y/%m/%d')

    def get_created_time_jalali(self, obj):
        jalali_datetime = jdatetime.datetime.fromgregorian(
            datetime=obj.created_datetime, locale='fa_IR')
        return jalali_datetime.strftime('%H:%M')

    def get_invoie_items(self, obj):
        user = self.context.get('request').user
        items = obj.items.filter(
            product__FK_Shop__FK_ShopManager=user).order_by('product__FK_Shop')
        return InvoiceItemSerializer(items, many=True, read_only=True).data

    def get_invoice_price_with_discount(self, obj):
        user = self.context.get('request').user
        total = 0
        for item in obj.items.filter(product__FK_Shop__FK_ShopManager=user):
            price = item.product.Price
            total += price
        return total

    def get_invoice_price_without_discount(self, obj):
        user = self.context.get('request').user
        total = 0
        for item in obj.items.filter(product__FK_Shop__FK_ShopManager=user):
            oldprice = item.product.OldPrice
            price = item.product.Price
            total += oldprice or price
        return total

    class Meta:
        model = Invoice
        fields = (
            'id',
            'items',
            'address',
            'address_json',
            'user',
            'payment_unique_id',
            'status',
            'invoice_price_with_discount',
            'invoice_price_without_discount',
            'coupon_usages',
            'logistic_price',
            'logistic_errors',
            'final_price',
            'created_date_jalali',
            'created_time_jalali',
            'coupons_total_price',
            'payment_request_datetime',
            'receiver_mobile_number',
            'logistic_unit_details',
        )


class BarcodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = ('barcode', )
