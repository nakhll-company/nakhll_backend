from django.shortcuts import get_object_or_404
from accounting_new.models import Invoice
from logistic.serializers import AddressSerializer
from nakhll_market.serializer_fields import Base64ImageField
from restapi.serializers import BigCitySerializer, CitySerializer, ProfileImageSerializer, ProfileSerializer, ShopBannerSerializer, UserDetailSerializer
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import fields, query
from rest_framework import serializers
from rest_framework.relations import HyperlinkedIdentityField, HyperlinkedRelatedField
from rest_framework.utils import field_mapping
from nakhll_market.models import (
    Alert, AmazingProduct, AttrPrice, AttrProduct, Attribute, BankAccount, BigCity, City, NewCategory, ShopBankAccount, ShopSocialMedia,
    Category, Market, PostRange, Product, ProductBanner, Profile, Shop, ShopBankAccount, Slider, Comment, State,
    SubMarket, LandingPageSchema, ShopPageSchema,
    )

# landing serializers
class SliderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slider
        fields = [
            'url', 'image', 'title', 'show_info', 'description', 'location',
            ]

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 
        ]

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            'id', 'Slug', 'title', 'url', 'image_thumbnail',
        ]


class NewCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = NewCategory
        fields = ['id', 'name', 'order', 'slug']

class NewCategoryProductCountSerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()
    class Meta:
        model = NewCategory
        fields = ['id', 'name', 'order', 'slug', 'product_count']

    def get_product_count(self, obj):
        return obj.product_count

class NewCategoryChildSerializer(serializers.ModelSerializer):
    childrens = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = NewCategory
        fields = ['id', 'name', 'order', 'slug', 'childrens']

    def get_childrens(self, obj):
        max_depth = self.context.get('max_depth', -1) - 1
        if max_depth == 0:
            return []
        context = {'max_depth': max_depth}
        return NewCategoryChildSerializer(obj.childrens, many=True, context=context).data

class NewCategoryParentSerializer(serializers.ModelSerializer):
    parents = serializers.SerializerMethodField(read_only=True, method_name='parents_to_root')
    class Meta:
        model = NewCategory
        fields = ['id', 'name', 'order', 'slug', 'parents']

    def parents_to_root(self, obj):
        parents = []
        parent = obj.parent
        while parent:
            parents.append(parent)
            parent = parent.parent
        return NewCategorySerializer(parents, many=True).data

class NewCategoryParentChildSerializer(serializers.ModelSerializer):
    parents = serializers.SerializerMethodField(read_only=True, method_name='parents_to_root')
    childrens = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = NewCategory
        fields = ['id', 'name', 'order', 'slug', 'parents', 'childrens']

    def parents_to_root(self, obj):
        return NewCategoryParentSerializer(NewCategory.objects.parents_to_root(obj), many=True).data    

    def get_childrens(self, obj):
        max_depth = self.context.get('max_depth', -1) - 1
        context = {'max_depth': max_depth}
        return NewCategoryChildSerializer(obj.childrens, many=True, context=context).data

   


class ShopSerializer(serializers.ModelSerializer):
    registered_months = serializers.SerializerMethodField()
    FK_ShopManager = UserSerializer(read_only=True)
    profile = ProfileImageSerializer(read_only=True)
    banners = ShopBannerSerializer(many=True, read_only=True)
    class Meta:
        model = Shop
        fields = [
            'ID', 'slug', 'title', 'image_thumbnail_url', 'total_products',
            'state', 'big_city', 'city', 'registered_months', 'FK_ShopManager',
            'is_landing', 'has_product_group_add_edit_permission',
            'banners', 'profile',
        ]
    def get_registered_months(self, obj):
        ''' Calculate months from DateCreate till now '''
        return (timezone.now() - obj.DateCreate).days // 30

class ShopSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ['ID', 'slug', 'title', ]

class CreateShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ['Slug', 'Title', 'State', 'BigCity', 'City', 'show_contact_info']
        extra_kwargs = {
            'Slug': {'validators': [], 'allow_null': True, 'required': False}
        }
   

class FilterPageShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ['ID', 'slug', 'title', 'state']

class ProductSerializer(serializers.ModelSerializer):
    FK_Shop = FilterPageShopSerializer(many=False, read_only=True)
    class Meta:
        model = Product
        fields = [
            'Image_medium_url', 'OldPrice', 'Price', 'Slug',
            'Title', 'discount', 'ID', 'FK_Shop', 'discount', 'is_advertisement'
        ]

class AmazingProductSerializer(serializers.ModelSerializer):
    product = ProductSerializer(many=False, read_only=True)
    class Meta:
        model = AmazingProduct
        fields = [
            'product', 'start_date_field', 'end_date_field'
        ]

# product page serializer
class AttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attribute
        fields = [
            'title', 'unit'
        ]

class AttrProductSerializer(serializers.ModelSerializer):
    FK_Attribute = AttributeSerializer(many=False, read_only=True)
    class Meta:
        model = AttrProduct
        fields = [
            'FK_Attribute', 'value'
        ]

class AttrPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttrPrice
        fields = [
            'description', 'id', 'value', 'extra_price', 'unit',
            'available', 'publish',
        ]

class ProductBannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductBanner
        fields = [
            'image', 'id'
        ]

class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(many=False, read_only=True)
    class Meta:
        model = Comment
        fields = [
            'user', 'description', 'number_like',
            'date_create',
        ]

class ProductCommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(many=False, read_only=True)
    reply = CommentSerializer(many=False, read_only=True)
    comment_replies = serializers.SerializerMethodField()
    class Meta:
        model = Comment
        fields = [
            'user', 'description', 'number_like',
            'reply', 'date_create', 'comment_replies',
        ]

    def get_comment_replies(self, obj):
        if obj.Comment_Pater:
            replies = obj.Comment_Pater
            return CommentSerializer(replies, many=True).data
class MarketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Market
        fields = [
            'title', 'url', 'id',
        ]

class SubMarketProductSerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()
    class Meta:
        model = SubMarket
        fields = [
            'title', 'url', 'id', 'product_count'
        ]
    def get_product_count(self, obj):
        return obj.product_count


class SubMarketSerializer(serializers.ModelSerializer):
    market = MarketSerializer(many=False, read_only=False)
    class Meta:
        model = SubMarket
        fields = [
            'title', 'market', 'url', 'id'
        ]

class PostRangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostRange
        fields = [
            'state', 'big_city', 'city'
        ]

class SimplePostRangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostRange
        fields = ['city', ]


class ProductDetailSerializer(serializers.HyperlinkedModelSerializer):
    attributes = AttrProductSerializer(many=True, read_only=True)
    attributes_price = AttrPriceSerializer(many=True, read_only=True)
    banners = ProductBannerSerializer(many=True, read_only=True)
    sub_market = SubMarketSerializer(many=False, read_only=True)
    shop = ShopSerializer(many=False, read_only=False)
    post_range = PostRangeSerializer(many=True, read_only=True)
    exception_post_range = PostRangeSerializer(many=True, read_only=True)
    new_category = NewCategoryParentSerializer(many=False, read_only=True)
    class Meta:
        model = Product
        fields = [
            'id', 'title', 'description', 'slug', 'price', 'old_price',
            'available', 'publish', 'discount', 'shop', 'image',
            'attributes', 'attributes_price', 'banners', 'inventory',
            'net_weight', 'weight_with_packing',  'length_with_packing',
            'height_with_packaging', 'story', 'width_with_packing', 'PreparationDays',
            'status', 'exception_post_range', 'post_range', 'sub_market', 'new_category'
        ]

class ProductListSerializer(serializers.ModelSerializer):
    FK_Shop = FilterPageShopSerializer(read_only=True)
    class Meta:
        model = Product
        fields = [
            'ID',
            'Title',
            'Slug',
            'Inventory',
            'Image_medium_url',
            'FK_Shop',
            'Price',
            'OldPrice',
            'discount',
            'is_advertisement',
        ]
    # Image = serializers.SerializerMethodField(method_name='get_absolute_image_url')
    # def get_absolute_image_url(self, product):
        # request = self.context.get('request')
        # photo_url = product.Image.url if product.Image else None
        # return request.build_absolute_uri(photo_url)

class ProductOwnerListSerializer(serializers.ModelSerializer):
    FK_Shop = FilterPageShopSerializer(read_only=True)
    post_range_cities = serializers.SlugRelatedField(slug_field='name', read_only=True, many=True)
    class Meta:
        model = Product
        fields = [
            'ID',
            'Title',
            'Slug',
            'Inventory',
            'Image_medium_url',
            'image_thumbnail_url',
            'FK_Shop',
            'Price',
            'OldPrice',
            'discount',
            'is_advertisement',
            'Status',
            'PreparationDays',
            'Available',
            'Publish',
            'new_category_id',
            'post_range_cities'
        ]

class ProductSubMarketSerializer(serializers.Serializer):
    product = serializers.UUIDField()
    submarkets = serializers.ListField(
        child=serializers.UUIDField()
    )

class ProductImagesSerializer(serializers.Serializer):
    product = serializers.UUIDField()
    images = serializers.ListField(
        child=Base64ImageField(max_length=None, use_url=True)
    )

class ProductBannerSerializer(serializers.ModelSerializer):
    FK_Product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), pk_field=serializers.UUIDField(format='hex'))
    Image = Base64ImageField(max_length=None, use_url=True)
    class Meta:
        model = ProductBanner
        fields = [
            'id', 'Image', 'FK_Product'
        ]



class Base64ImageSerializer(serializers.Serializer):
    image = Base64ImageField(max_length=None, use_url=True)

class ProductUpdateSerializer(serializers.ModelSerializer):
    # FK_Shop = serializers.SlugRelatedField(slug_field='Slug', many=False, read_only=True)
    # FK_SubMarket = serializers.PrimaryKeyRelatedField(read_only=False, many=False, queryset=SubMarket.objects.all())
    new_category = serializers.PrimaryKeyRelatedField(read_only=False, many=False, queryset=NewCategory.objects.all())
    Product_Banner = serializers.PrimaryKeyRelatedField(queryset=ProductBanner.objects.all(), many=True, read_only=False)
    post_range = serializers.PrimaryKeyRelatedField(source='post_range_cities', read_only=False, many=True, queryset=City.objects.all())
    class Meta:
        model = Product
        fields = [
            'ID',
            'Title',
            'Inventory',
            'Price',
            'OldPrice',
            'Net_Weight',
            'Weight_With_Packing',
            'Description',
            'Status',
            'PostRangeType',
            'PreparationDays',
            # 'FK_SubMarket',
            'new_category',
            'Product_Banner',
            'post_range'
        ]
    def update(self, instance, validated_data):
        # Direct assignment to the reverse side of a related set is prohibited, 
        # so I am deleteing related ProductBanner objects to clean database from
        # ProductBanners that have no Product assigned to
        product_banners = validated_data.pop('Product_Banner')
        deleted_banners = [banner.delete() 
                           for banner in instance.Product_Banner.all() 
                           if banner not in product_banners]

        product_post_ranges = validated_data.pop('post_range_cities')
        instance.post_range_cities.clear()
        instance.post_range_cities.add(*product_post_ranges)

        for prop in validated_data:
            setattr(instance, prop, validated_data[prop])
        instance.save()
        return instance


class ProductWriteSerializer(serializers.ModelSerializer):
    FK_Shop = serializers.SlugRelatedField(slug_field='Slug', many=False, read_only=False, queryset=Shop.objects.all())
    new_category = serializers.PrimaryKeyRelatedField(read_only=False, many=False, queryset=NewCategory.objects.all())
    post_range = serializers.PrimaryKeyRelatedField(source='post_range_cities', read_only=False, many=True, queryset=City.objects.all())
    class Meta:
        model = Product
        fields = [
            'ID',
            'Title',
            'Inventory',
            'Price',
            'OldPrice',
            'Net_Weight',
            'Weight_With_Packing',
            'Description',
            'Status',
            'PostRangeType',
            'PreparationDays',
            'FK_Shop',
            'new_category',
            'post_range'
        ]

class FullMarketSerializer(serializers.ModelSerializer):
    submarkets = SubMarketSerializer(many=True, read_only=True)
    # submarkets = serializers.SerializerMethodField()
    def get_submarkets(self, obj):
        query = self.context.get('query')
        return [submarket.id for submarket in obj.submarkets.all()]
    class Meta:
        model = Market
        fields = [
            'id',
            'title',
            'description',
            'image',
            'slug',
            'url',
            'submarkets',
        ]


class ProductCategorySerializer(serializers.Serializer):
    product = serializers.UUIDField()
    categories = serializers.ListField(
        child=serializers.IntegerField(min_value=0)
    )


class ShopFullSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True, many=False)
    sub_market = SubMarketSerializer(read_only=True, many=True)
    class Meta:
        model = Shop
        fields = [
            'title', 'slug', 'url', 'description', 'profile', 'image_thumbnail_url',
            'state', 'sub_market',
        ]

class ShopBankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopBankAccount
        fields = ['iban', 'owner']
class ShopSocialMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopSocialMedia
        fields = ['telegram', 'instagram']

class SettingsProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['NationalCode', 'MobileNumber', 'PhoneNumber', 'State', 'BigCity', 'City', 'Address', 'ZipCode']
        extra_kwargs = {
            'NationalCode': {'validators': []},
            'MobileNumber': {'validators': []}
        }

class UserProfileSerializer(serializers.ModelSerializer):
    User_Profile = SettingsProfileSerializer(read_only=False)
    class Meta:
        model = User
        fields = ['User_Profile']
class ShopSettingsSerializer(serializers.ModelSerializer):
    FK_ShopManager = UserProfileSerializer(read_only=False)
    class Meta:
        model = Shop
        fields = [
            'Title', 'Slug', 'Description', 'FK_ShopManager', 
        ]
        extra_kwargs = {
            'Slug': {'validators': []},
        }

class ShopAllSettingsSerializer(serializers.ModelSerializer):
    FK_ShopManager = UserProfileSerializer(read_only=False)
    bank_account = ShopBankAccountSerializer(read_only=True)
    social_media = ShopSocialMediaSerializer(read_only=True)
    class Meta:
        model = Shop
        fields = [
            'Title', 'Slug', 'Description', 'FK_ShopManager', 'bank_account', 'social_media', 'image_thumbnail_url' 
        ]
        extra_kwargs = {
            'Slug': {'validators': []},
        }
    def update(self, instance, validated_data):
        user = validated_data.get('FK_ShopManager')
        if not user:
            return instance

        profile_data = user.get('User_Profile')
        if not profile_data:
            return instance

        instance.Title = validated_data.get('Title')
        instance.Description = validated_data.get('Description')

        profile = instance.FK_ShopManager.User_Profile
        profile.NationalCode = profile_data.get('NationalCode')
        profile.MobileNumber = profile_data.get('MobileNumber')
        profile.PhoneNumber = profile_data.get('PhoneNumber')
        profile.State = profile_data.get('State')
        profile.BigCity = profile_data.get('BigCity')
        profile.City = profile_data.get('City')
        profile.Address = profile_data.get('Address')
        profile.ZipCode = profile_data.get('ZipCode')

        profile.save()
        instance.save()
        return instance
            
class ShopBankAccountSettingsSerializer(serializers.ModelSerializer):
    bank_account = ShopBankAccountSerializer(read_only=False)
    class Meta:
        model = Shop
        fields = ['bank_account', ]
    def update(self, instance, validated_data):
        bank_account_data = validated_data.get('bank_account')
        if not bank_account_data:
            return instance
        bank_account, created = ShopBankAccount.objects.get_or_create(shop=instance)
        bank_account.iban = bank_account_data.get('iban')
        bank_account.owner = bank_account_data.get('owner')
        bank_account.save()
        return instance
 
class SocialMediaAccountSettingsSerializer(serializers.ModelSerializer):
    social_media = ShopSocialMediaSerializer(read_only=False)
    class Meta:
        model = Shop
        fields = ['social_media', ]
    def update(self, instance, validated_data):
        social_media_data = validated_data.get('social_media')
        if not social_media_data:
            return instance
        social_media, created = ShopSocialMedia.objects.get_or_create(shop=instance)
        social_media.telegram = social_media_data.get('telegram')
        social_media.instagram = social_media_data.get('instagram')
        social_media.save()
        return instance
 


 

class ProductPriceWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['Slug', 'OldPrice', 'Price' ] 
        extra_kwargs = {
            'Slug': {'validators': []},
        }

class ProductInventoryWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['Slug', 'Inventory'] 
        extra_kwargs = {
            'Slug': {'validators': []},
        }


class CityFullSerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ['id', 'name', ]


class BigCityFullSerializer(serializers.ModelSerializer):
    city = CityFullSerializer(read_only=True, many=True)
    class Meta:
        model = BigCity
        fields = ['id', 'name', 'city']

class StateFullSeraializer(serializers.ModelSerializer):
    big_city = BigCityFullSerializer(read_only=True, many=True)
    class Meta:
        model = State
        fields = ['id', 'name', 'big_city']

class ShopProductsSerializer(serializers.ModelSerializer):
    ShopProduct = ProductSerializer(read_only=True, many=True)
    class Meta:
        model = Shop
        fields = ['id', 'title', 'slug', 'url', 'image_thumbnail_url', 'state', 'ShopProduct']

class ShopProductSerializer(serializers.ModelSerializer):
    shop = ShopSerializer(read_only=True)
    class Meta:
        model = Product
        fields = ['id', 'title', 'slug', 'image_thumbnail_url', 'shop', 'price', 'old_price', 'discount',]

class NewProfileSerializer(serializers.ModelSerializer):
    wallet = serializers.ReadOnlyField(source='FK_User.WalletManager.Inverntory')
    FK_User = UserSerializer(many=False, read_only=False)
    Image = Base64ImageField(max_length=None, use_url=True, allow_empty_file=False, required=False)
    class Meta:
        model = Profile
        fields = ['id', 'NationalCode', 'MobileNumber', 'FK_User', 'BrithDay', 'Image', 'wallet', 'State', 'BigCity', 'City', 'Sex', 'Bio', 'image']
        read_only_fields = ['MobileNumber']
        extra_kwargs = {
            'NationalCode': {'validators': []},
        }
        
    def update(self, instance, validated_data):
        if 'Image' in validated_data:
            instance.Image = validated_data.pop('Image')

        user = validated_data.pop('FK_User')
        instance.user.first_name = user.get('first_name')
        instance.user.last_name = user.get('last_name')
        for prop in validated_data:
            setattr(instance, prop, validated_data[prop])
        instance.user.save()
        instance.save()
        return instance

class LandingPageSchemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandingPageSchema
        fields = ['component_type', 'data', 'title', 'subtitle', 'url', 'background_color',
                'image', 'publish_status', 'order']

class ShopPageSchemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopPageSchema
        fields = ['component_type', 'data', 'title', 'subtitle', 'url', 'background_color',
                'image', 'publish_status', 'order', 'shop']

class ProductThumbnailSerializers(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'title', 'slug', 'image_thumbnail_url', 'price', 'old_price', 'discount',]

class UserOrderSerializer(serializers.ModelSerializer):
    products = ProductSerializer(read_only=True, many=True)
    receiver_name = serializers.ReadOnlyField(source='address.receiver_full_name')
    receiver_mobile = serializers.ReadOnlyField(source='address.receiver_mobile_number')
    address = AddressSerializer(read_only=True)
    class Meta:
        model = Invoice
        fields = ('id', 'FactorNumber', 'products', 'address_json', 'address', 'created_datetime', 
                  'final_invoice_price', 'final_coupon_price', 'final_logistic_price', 'status',
                  'receiver_name', 'receiver_mobile')

class ProductLastStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['Price', 'OldPrice', 'Status', 'PreparationDays', 'Publish', 'Title']


class ShopSlugSerializer(serializers.ModelSerializer):
    products = serializers.SerializerMethodField()
    class Meta:
        model = Shop
        fields = ('Slug', 'products')
    
    def get_products(self, obj):
        return obj.products
