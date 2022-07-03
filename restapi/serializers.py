from os import read
from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from django.contrib.auth.models import User
from nakhll_market.models import (Profile , Product , Shop , 
                                State, BigCity, City, ProductBanner)
import re
from rest_framework.exceptions import  ValidationError 
from rest_framework.fields import CurrentUserDefault








class ShopListHomeSerializer(ModelSerializer):
    class Meta:
        model = Shop
        fields = [
            'id',
            'title',
            'slug',
            'image_thumbnail_url',
            'image_thumbnail_url',
            'point',
            'available',
            'publish',
            'is_landing',
            'has_product_group_add_edit_permission',
        ]


# user and profile and home page 
class UserDetailSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
        ]
        read_only_fields = [
            'username',
        ]

class ShopDetailSerializer(ModelSerializer):
    FK_ShopManager = UserDetailSerializer(read_only = True)
    class Meta:
        model = Shop
        fields = [
            'ID',
            'Title',
            'Slug',
            'Description',
            'Image_thumbnail_url',
            'Bio',
            'State',
            'BigCity',
            'City',
            'Point',
            'Holidays',
            'Available',
            'FK_ShopManager',
            'Publish',
        ]


class ProfileSerializer(ModelSerializer):
    user = UserDetailSerializer(read_only = True)
    shops = ShopListHomeSerializer(many=True)
    cart_items_count = serializers.SerializerMethodField()

    class Meta:
        model = Profile 
        fields = [
            'id',
            'user',
            'sex',
            'birth_day',
            'counter_pre_code',
            'mobile_number',
            'zip_code',
            'national_code',
            'address',
            'state',
            'big_city',
            'city',
            'location',
            'bio',
            'phone_number',
            'image',
            'fax_number',
            'city_per_code',
            'image_national_card',
            'referral_link',
            'point',
            'tutorial_website',
            'reference_code',
            'ip_address',
            'shops',
            'cart_items_count'
        ]

    def get_cart_items_count(self, obj):
        try:
            return obj.user.cart.items.count()
        except:
            return 0



class SimpleProfileSerializer(ModelSerializer):
    user = UserDetailSerializer(read_only = True)
    class Meta:
        model = Profile 
        fields = [
            'id',
            'user',
            'sex',
            'mobile_number',
            'national_code',
            'image',
        ]


class ProductListHomeSerializer(ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'ID',
            'Title',
            'Slug',
            'Image_medium_url',
            'Price',
            'OldPrice',
            'Point',
            'Available',
            'Publish',
        ]

class ProductFullSerializer(ModelSerializer):
    FK_Shop = ShopDetailSerializer(read_only = True)
    class Meta:
        model = Product
        fields = [
            'Title',
            'FK_Shop',
        ]

class ProductTitleSerializer(ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'Title'
        ]


class SimpleProductSerializer(ModelSerializer):
    shop = serializers.SlugRelatedField(read_only = True, slug_field = 'Slug')
    class Meta:
        model = Product
        fields = [
            'shop',
            'title',
            'price', 
            'old_price',
            'discount',
            'image_thumbnail_url',
        ]


class FilteredFactorPostListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        user = self.context.get('request').user
        data = data.filter(FK_Product__FK_Shop__FK_ShopManager = user)
        return super(FilteredFactorPostListSerializer, self).to_representation(data)


class ProductBannerSerializer(ModelSerializer):
    class Meta:
        model = ProductBanner
        fields = [
            'id',
            'Image',
        ]



# //////////// web cart navbar view
class ShopCartView(ModelSerializer):
    class Meta:
        model = Shop
        fields = [
            'Slug',
        ]

class ProductCartView(ModelSerializer):
    FK_Shop = ShopCartView(read_only=True)
    class Meta:
        model = Product
        fields = [
            'Title',
            'Slug',
            'FK_Shop',
            'Image_thumbnail_url'
        ]

class ShopDetailForPoint(ModelSerializer):
    class Meta:
        model = Shop
        fields = [
            'ID',
            'Title',
            'Image_thumbnail_url',
            'get_url',
        ]

class PointSerializer(ModelSerializer):
    FK_Shop = ShopDetailForPoint(read_only = True)
    class Meta:
        model = Product
        fields = [
            'ID',
            'Title',
            'get_url',
            'Image_thumbnail_url',
            'FK_Shop',
        ]

class ProductSerializer(ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'ID',
            'Title',
            'Slug',
            'Image_medium_url',
            'Price',
            'Status',
        ]

class StateSerializer(ModelSerializer):
    class Meta:
        model = State
        fields = ['id', 'name', ]

class BigCitySerializer(ModelSerializer):
    class Meta:
        model = BigCity
        fields = ['id', 'name', ]

class CitySerializer(ModelSerializer):
    class Meta:
        model = City
        fields = ['id', 'name', 'value', 'label']


class ProfileImageSerializer(ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            'Image_thumbnail_url',
        ]


