from rest_framework import serializers
from cart.models import Cart, CartItem
from coupon.models import Coupon
from coupon.serializers import CouponSerializer
from logistic.models import Address
from logistic.serializers import AddressReadSerializer
from nakhll_market.models import Product
from nakhll_market.serializers import ProductSerializer



class CartItemSerializer(serializers.ModelSerializer):
    cart = serializers.PrimaryKeyRelatedField(read_only=True)
    product = serializers.PrimaryKeyRelatedField(many=False, read_only=False, queryset=Product.objects.all())
    class Meta:
        model = CartItem
        fields = ('cart', 'product', 'count', 'added_datetime', )
        read_only_fields = ('product_last_state', )

    def create(self, validated_data):
        cart = validated_data.pop('cart')
        product = validated_data.pop('product')
        return cart.add_product(product)
        


class CartItemReadSerializer(serializers.ModelSerializer):
    cart = serializers.PrimaryKeyRelatedField(read_only=True)
    product = ProductSerializer(read_only=True, many=False)
    total_price = serializers.SerializerMethodField()
    total_old_price = serializers.SerializerMethodField()

    def get_total_old_price(self, obj):
        return obj.product.old_price * obj.count

    def get_total_price(self, obj):
        return obj.product.price * obj.count
    class Meta:
        model = CartItem
        fields = '__all__'
        read_only_fields = ('product_last_state', )





class CartSerializer(serializers.ModelSerializer):
    ordered_items = CartItemReadSerializer(many=True, read_only=True)
    count = serializers.SerializerMethodField()
    address = AddressReadSerializer(read_only=True)
    coupon_details = serializers.SerializerMethodField()
    class Meta:
        model = Cart
        fields = ('user', 'cart_price', 'cart_old_price',
                  'address', 'logistic_details', 'coupon_details',
                  'ordered_items', 'count', 'total_price')
    
    def get_count(self, object):
        return object.items.count()

    def get_coupon_details(self, cart):
        coupons = cart.get_coupons_price()
        total_price = sum([coupon['price'] for coupon in coupons])
        return {'total': total_price, 'coupons': coupons}


class CartWriteSerializer(serializers.ModelSerializer):
    address = serializers.PrimaryKeyRelatedField(queryset=Address.objects.all(), required=False)
    coupon = serializers.SlugRelatedField(slug_field='code', error_messages={
        'does_not_exist': 'کوپن تخفیف وارد شده نامعتبر است',
    }, required=False, queryset=Coupon.objects.all())

    class Meta:
        model = Cart
        fields = (
            'address',
            'coupon',
        )