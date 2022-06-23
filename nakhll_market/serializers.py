from attr import validate
from django.utils import timezone
from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from invoice.models import Invoice
from logistic.serializers import AddressSerializer
from nakhll.utils import get_dict, generate_unique_slug
from nakhll_market.serializer_fields import Base64ImageField
from nakhll_market.validators import validate_iran_national_code
from restapi.serializers import (
    BigCitySerializer,
    CitySerializer,
    ProfileImageSerializer,
    ProfileSerializer,
    StateSerializer)
from nakhll_market.models import (
    BigCity, City, Comment, Category, ShopBankAccount, ShopSocialMedia,
    Product, ProductBanner, Profile, Shop, Slider, State,
    LandingPageSchema, ShopPageSchema, UserImage, Tag, ProductTag,
)
from nakhll_market.mixins import DriveBigCityAndStateFromCityMixin
from shop.models import ShopFeature
from shop.serializers import ShopLandingDetailsSerializer
import jdatetime


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name',
        ]


class SliderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slider
        fields = [
            'url', 'image', 'title', 'show_info', 'description', 'location',
        ]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'order', 'slug']


class CategoryProductCountSerializer(serializers.ModelSerializer):
    ''' Represents the product count of a category '''
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'order', 'slug', 'product_count']

    def get_product_count(self, obj):
        return obj.products_count


class CategoryChildSerializer(serializers.ModelSerializer):
    ''' Represents the child categories of a category '''
    childrens = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'order', 'slug', 'childrens']

    def get_childrens(self, obj):
        max_depth = self.context.get('max_depth', -1) - 1
        if max_depth == 0:
            return []
        context = {'max_depth': max_depth}
        return CategoryChildSerializer(
            obj.childrens, many=True, context=context).data


class CategoryParentSerializer(serializers.ModelSerializer):
    ''' Represents the parent categories of a category to root '''
    parents = serializers.SerializerMethodField(
        read_only=True, method_name='parents_to_root')

    class Meta:
        model = Category
        fields = ['id', 'name', 'order', 'slug', 'parents']

    def parents_to_root(self, obj):
        parents = []
        parent = obj.parent
        while parent:
            parents.append(parent)
            parent = parent.parent
        return CategorySerializer(parents, many=True).data


class CategoryParentChildSerializer(serializers.ModelSerializer):
    ''' Represents both the childs and the parent categories of a category to root '''
    parents = serializers.SerializerMethodField(
        read_only=True, method_name='parents_to_root')
    childrens = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'order', 'slug', 'parents', 'childrens']

    def parents_to_root(self, obj):
        return CategoryParentSerializer(
            Category.objects.parents_to_root(obj),
            many=True).data

    def get_childrens(self, obj):
        max_depth = self.context.get('max_depth', -1) - 1
        context = {'max_depth': max_depth}
        return CategoryChildSerializer(
            obj.childrens, many=True, context=context).data


class ShopSerializer(serializers.ModelSerializer):
    registered_months = serializers.SerializerMethodField()
    FK_ShopManager = UserSerializer(read_only=True)
    profile = ProfileImageSerializer(read_only=True)
    landing_data = serializers.SerializerMethodField()
    is_landing = serializers.SerializerMethodField()
    yektanet_advertisement = serializers.SerializerMethodField()
    state = StateSerializer(read_only=True)
    big_city = BigCitySerializer(read_only=True)
    city = CitySerializer(read_only=True)

    class Meta:
        model = Shop
        fields = [
            'ID',
            'slug',
            'title',
            'image_thumbnail_url',
            'total_products',
            'Description',
            'registered_months',
            'FK_ShopManager',
            'is_landing',
            'has_product_group_add_edit_permission',
            'profile',
            'landing_data',
            'yektanet_advertisement',
            'in_campaign',
            'state',
            'big_city',
            'city']

    def get_registered_months(self, obj):
        ''' Calculate months from DateCreate till now '''
        return (timezone.now() - obj.DateCreate).days // 30

    def get_is_landing(self, obj):
        # TODO: Remove this IMMEDIATELY
        if obj.Slug == 'neil-market-food-store':
            return True
        return False

    def get_landing_data(self, obj):
        if ShopFeature.has_shop_landing_access(
                obj) and ShopFeature.has_active_landing_page(obj):
            return ShopLandingDetailsSerializer(obj.get_active_landing()).data
        return None

    def get_yektanet_advertisement(self, obj):
        if obj.has_advertisement():
            ads = obj.get_advertisement()
            return ads.yektanet_id
        return None


class ShopSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ['ID', 'slug', 'title', ]


class CreateShopSerializer(
    DriveBigCityAndStateFromCityMixin, 
    serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=127, write_only=True)
    last_name = serializers.CharField(max_length=127, write_only=True)

    class Meta:
        model = Shop
        fields = [
            'Title',
            'Slug',
            'City',
            'show_contact_info',
            'first_name',
            'last_name']
        extra_kwargs = {
            'Slug': {'validators': [], 'allow_null': True, 'required': False}
        }

    def validate_first_name(self, value):
        user = self.context.get('request').user
        return user.first_name or value

    def validate_last_name(self, value):
        user = self.context.get('request').user
        return user.last_name or value

    def validate(self, data):
        title = data.get('Title')
        slug = data.get('Slug')
        if not slug:
            slug = generate_unique_slug(Shop, title, slug_field='Slug')
        elif Shop.objects.filter(Slug=slug).exists():
            raise ValidationError({'details': 'شناسه حجره از قبل موجود است'})
        data['Slug'] = slug
        return data

class FilterPageShopSerializer(serializers.ModelSerializer):
    state = StateSerializer()

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


class ProductBannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductBanner
        fields = [
            'image', 'id'
        ]


class ProductDetailSerializer(serializers.HyperlinkedModelSerializer):
    banners = ProductBannerSerializer(many=True, read_only=True)
    shop = ShopSerializer(many=False, read_only=False)
    category = CategoryParentSerializer(many=False, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'title',
            'description',
            'slug',
            'price',
            'old_price',
            'available',
            'salable',
            'discount',
            'shop',
            'image',
            'banners',
            'inventory',
            'status',
            'exception_post_range',
            'category',
            'net_weight',
            'weight_with_packing',
            'length_with_packing',
            'height_with_packaging',
            'story',
            'width_with_packing',
            'PreparationDays',
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

    def get_shop_in_campaign(self, obj):
        if obj.shop.in_campaign:
            return True
        return False


class ProductListSerializer(serializers.ModelSerializer):
    FK_Shop = FilterPageShopSerializer(read_only=True)
    in_campaign = serializers.SerializerMethodField()

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
            'in_campaign',
        ]

    def get_in_campaign(self, obj):
        if obj.FK_Shop.in_campaign:
            return True
        return False


class ProductOwnerListSerializer(serializers.ModelSerializer):
    FK_Shop = FilterPageShopSerializer(read_only=True)
    post_range_cities = serializers.SlugRelatedField(
        slug_field='name', read_only=True, many=True)

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
            'category_id',
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


class ProductBannerWithProductSerializer(serializers.ModelSerializer):
    FK_Product = serializers.SlugRelatedField(
        queryset=Product.objects.all(), slug_field='Slug')
    Image = Base64ImageField(max_length=None, use_url=True)

    class Meta:
        model = ProductBanner
        fields = [
            'id', 'Image', 'FK_Product'
        ]


class Base64ImageSerializer(serializers.Serializer):
    image = Base64ImageField(max_length=None, use_url=True)


class ProductTagWriteSerializer(serializers.ModelSerializer):
    text = serializers.CharField(source="tag")

    class Meta:
        model = ProductTag
        fields = ['id', 'text', ]

    def validate_text(self, data):
        if len(data) > 127:
            raise serializers.ValidationError(
                {'error': 'تعداد کاراکترهای تگ انتخاب شده بیش از حد مجاز است.'})
        return data


class TagOwnerListSerializer(serializers.ModelSerializer):
    text = serializers.CharField(source="name")

    class Meta:
        model = Tag
        fields = ['id', 'text', 'shop']


class ProductBannerWriteSerializer(serializers.ModelSerializer):
    Image = Base64ImageField(max_length=None, use_url=True)

    class Meta:
        model = ProductBanner
        fields = ['id', 'Image']


class ProductOwnerWriteSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        read_only=False,
        many=False,
        queryset=Category.objects.all(),
        required=True,
        error_messages={
            'required': ' کتگوری را انتخاب کنید',
            'null': 'کتگوری را انتخاب کنید'})
    product_tags = ProductTagWriteSerializer(
        many=True, read_only=False, required=False)
    Image = Base64ImageField(max_length=None, use_url=True, error_messages={
        'null': 'لطفا تصویر را انتخاب کنید',
        'required': 'لطفا تصویر را انتخاب کنید'
    })
    Product_Banner = ProductBannerWriteSerializer(many=True, read_only=False)
    post_range = serializers.PrimaryKeyRelatedField(
        source='post_range_cities', read_only=False, many=True,
        queryset=City.objects.all())

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
            'Image',
            'Product_Banner',
            'PostRangeType',
            'PreparationDays',
            'category',
            'post_range',
            'product_tags',
        ]

    def create(self, validated_data):
        banners = validated_data.pop('Product_Banner')
        tags_list: list = [x['tag']
                           for x in validated_data.pop('product_tags', [])]
        post_range_cities = validated_data.pop('post_range_cities')
        instance = Product.objects.create(**validated_data)
        self.__tag_create(instance, tags_list)
        instance.post_range_cities.add(*post_range_cities)
        banners = [ProductBanner.objects.create(
            FK_Product=instance, Image=banner['Image'])
            for banner in banners]
        instance.Product_Banner.add(*banners)
        return instance

    @staticmethod
    def __tag_create(instance, tags_list):
        if tags_list:
            all_tags = Tag.objects.filter(
                shop=instance.shop).values_list(
                'name', flat=True)
            new_tag = []
            for item in tags_list:
                if item not in all_tags:
                    new_tag.append(item)
            Tag.objects.bulk_create(
                [Tag(name=tag, shop=instance.shop) for tag in new_tag])
            tags = Tag.objects.filter(name__in=tags_list, shop=instance.shop)
            ProductTag.objects.bulk_create([
                ProductTag(
                    product=instance, tag=tag)
                for tag in tags])

    @staticmethod
    def __update_tags(instance: Product, validated_data):
        instance.product_tags.all().delete()
        tags_list = [x['tag'] for x in validated_data.pop('product_tags', [])]
        if tags_list:
            all_tags = Tag.objects.filter(
                shop=instance.shop).values_list(
                'name', flat=True)
            new_tag = []
            product_tags_id_list = ProductTag.objects.filter(
                product=instance).values_list('tag', flat=True)
            if product_tags_id_list:
                product_tags_list = get_dict(
                    Tag.objects.filter(
                        id__in=product_tags_id_list), 'name')
            else:
                product_tags_list = None

            tags_lst_b = tags_list.copy()
            for item in tags_list:
                if item not in all_tags:
                    new_tag.append(item)
                if product_tags_list and item in product_tags_list:
                    tags_lst_b.remove(item)
            tags_list = tags_lst_b
            if new_tag:
                Tag.objects.bulk_create([Tag(
                    name=tag, shop=instance.shop)
                    for tag in new_tag])
            if tags_list:
                tags = Tag.objects.filter(
                    name__in=tags_list, shop=instance.shop)
                ProductTag.objects.bulk_create([
                    ProductTag(
                        product=instance, tag=tag)
                    for tag in tags])

    def update(self, instance, validated_data):
        self.__update_banners(instance, validated_data)
        self.__update_tags(instance, validated_data)
        self.__update_post_range(instance, validated_data)
        for prop, value in validated_data.items():
            setattr(instance, prop, value)
        instance.save()
        return instance

    def __update_banners(self, instance, validated_data):
        if 'Product_Banner' not in validated_data:
            return
        instance.Product_Banner.clear()
        product_banners = [
            ProductBanner.objects.create(
                FK_Product=instance, Image=banner['Image'])
            for banner in validated_data.pop('Product_Banner')]
        instance.Product_Banner.add(*product_banners)

    def __update_post_range(self, instance, validated_data):
        if 'post_range_cities' not in validated_data:
            return
        instance.post_range_cities.clear()
        product_post_ranges = validated_data.pop('post_range_cities')
        instance.post_range_cities.add(*product_post_ranges)


class ProductOwnerReadSerializer(serializers.ModelSerializer):
    category = CategoryChildSerializer(many=False, read_only=True)
    Product_Banner = ProductBannerWriteSerializer(many=True, read_only=True)
    post_range = serializers.PrimaryKeyRelatedField(
        source='post_range_cities', read_only=True, many=True)
    product_tags = ProductTagWriteSerializer(many=True, read_only=False)
    all_tags = serializers.SerializerMethodField()

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
            'Image',
            'Product_Banner',
            'PostRangeType',
            'PreparationDays',
            'category',
            'post_range',
            'product_tags',
            'all_tags',
        ]

    def get_all_tags(self, obj):
        tags = Tag.objects.filter(shop=obj.shop)
        tags = TagOwnerListSerializer(tags, many=True).data
        return tags


class ProductCategorySerializer(serializers.Serializer):
    product = serializers.UUIDField()
    categories = serializers.ListField(
        child=serializers.IntegerField(min_value=0)
    )


class ShopFullSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True, many=False)

    class Meta:
        model = Shop
        fields = [
            'title',
            'slug',
            'url',
            'description',
            'profile',
            'image_thumbnail_url',
            'state',
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
        fields = [
            'NationalCode',
            'CityPerCode',
            'PhoneNumber',
            'State',
            'BigCity',
            'City',
            'Address',
            'ZipCode']
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
    FK_ShopManager = UserProfileSerializer(
        many=False, read_only=False, required=False)
    bank_account = ShopBankAccountSerializer(
        many=False, read_only=False, required=False)
    social_media = ShopSocialMediaSerializer(
        many=False, read_only=False, required=False)
    Image = Base64ImageField(
        max_length=None,
        use_url=True,
        allow_empty_file=False,
        required=False,
        allow_null=True)
    State = StateSerializer(many=False, read_only=False)
    BigCity = BigCitySerializer(many=False, read_only=False)
    City = CitySerializer(many=False, read_only=False)

    class Meta:
        model = Shop
        fields = [
            'Title',
            'Slug',
            'Image',
            'image_thumbnail_url',
            'bank_account',
            'social_media',
            'Description',
            'FK_ShopManager',
            'State',
            'BigCity',
            'City',
            'Location']
        read_only_fields = ['Title', 'Slug', 'image_thumbnail_url']

    def validate(self, data):
        if 'FK_ShopManager' in data:
            national_code = data['FK_ShopManager']['User_Profile'][
                'NationalCode']
            validate_iran_national_code(national_code)
            duplicated = Profile.objects.filter(NationalCode=national_code)
            if self.context.get('user'):
                duplicated = duplicated.exclude(
                    FK_User=self.context.get('user'))
            if duplicated.exists():
                raise serializers.ValidationError(
                    {'NationalCode_error': 'کد ملی وارد شده از قبل در سایت وجود دارد.'})
        state_name = data.pop(
            'State')['name'] if 'State' in data else None
        big_city_name = data.pop(
            'BigCity')['name'] if 'BigCity' in data else None
        city_name = data.pop(
            'City')['name'] if 'City' in data else None
        try:
            state = State.objects.get(name=state_name)
            big_city = BigCity.objects.get(name=big_city_name, state=state)
            city = City.objects.get(name=city_name, big_city=big_city)
            data['State'] = state
            data['BigCity'] = big_city
            data['City'] = city
        except State.DoesNotExist:
            raise serializers.ValidationError(
                {'error': 'استان انتخاب شده معتبر نمی باشد.'})
        except BigCity.DoesNotExist:
            raise serializers.ValidationError(
                {'error': 'شهرستان انتخاب شده معتبر نمی باشد.'})
        except City.DoesNotExist:
            raise serializers.ValidationError(
                {'error': 'شهر انتخاب شده معتبر نمی باشد.'})
        return data

    def update(self, instance, validated_data):
        profile = instance.FK_ShopManager.User_Profile
        user_data = validated_data.pop(
            'FK_ShopManager') if 'FK_ShopManager' in validated_data else {}
        profile_data = user_data.pop(
            'User_Profile') if 'User_Profile' in user_data else {}

        bank_account = instance.bank_account if hasattr(
            instance, 'bank_account') else ShopBankAccount.objects.create(
            shop=instance)
        bank_account_data = validated_data.pop(
            'bank_account') if 'bank_account' in validated_data else {}

        social_media = instance.social_media if hasattr(
            instance, 'social_media') else ShopSocialMedia.objects.create(
            shop=instance)
        social_media_data = validated_data.pop(
            'social_media') if 'social_media' in validated_data else {}

        image = validated_data.pop(
            'Image') if 'Image' in validated_data else None

        for prop in validated_data:
            setattr(instance, prop, validated_data[prop])
        if image:
            instance.Image = image
        instance.save()

        for prop in profile_data:
            setattr(profile, prop, profile_data[prop])
        profile.save()

        for prop in bank_account_data:
            setattr(bank_account, prop, bank_account_data[prop])
        bank_account.save()

        for prop in social_media_data:
            setattr(social_media, prop, social_media_data[prop])
        social_media.save()

        return instance


class ProductPriceWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['Slug', 'OldPrice', 'Price']
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
        fields = [
            'id',
            'title',
            'slug',
            'url',
            'image_thumbnail_url',
            'state',
            'ShopProduct']


class ShopProductSerializer(serializers.ModelSerializer):
    shop = ShopSerializer(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'title',
            'slug',
            'image_thumbnail_url',
            'shop',
            'price',
            'old_price',
            'discount',
        ]


class NewProfileSerializer(serializers.ModelSerializer):
    FK_User = UserSerializer(many=False, read_only=False)
    Image = Base64ImageField(
        max_length=None,
        use_url=True,
        allow_empty_file=False,
        required=False)

    class Meta:
        model = Profile
        fields = [
            'id',
            'NationalCode',
            'MobileNumber',
            'FK_User',
            'BrithDay',
            'Image',
            'State',
            'BigCity',
            'City',
            'Sex',
            'Bio',
            'image']
        read_only_fields = ['MobileNumber']
        extra_kwargs = {
            'NationalCode': {'validators': []},
        }

    def update(self, instance, validated_data):
        if 'Image' in validated_data:
            instance.Image = validated_data.pop('Image')
        user = validated_data.pop('FK_User')
        # TODO: I done as image for check birthday
        if 'BrithDay' in validated_data:
            birthday = validated_data.pop('BrithDay')
            instance.BrithDay = jdatetime.date(
                birthday.year, birthday.month, birthday.day)
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
        fields = [
            'component_type',
            'data',
            'title',
            'subtitle',
            'url',
            'background_color',
            'image',
            'publish_status',
            'order']


class ShopPageSchemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopPageSchema
        fields = [
            'component_type',
            'data',
            'title',
            'subtitle',
            'url',
            'background_color',
            'image',
            'publish_status',
            'order',
            'shop']


class ProductThumbnailSerializers(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'id',
            'title',
            'slug',
            'image_thumbnail_url',
            'price',
            'old_price',
            'discount',
        ]


class UserOrderSerializer(serializers.ModelSerializer):
    products = ProductSerializer(read_only=True, many=True)
    receiver_name = serializers.ReadOnlyField(
        source='address.receiver_full_name')
    receiver_mobile = serializers.ReadOnlyField(
        source='address.receiver_mobile_number')
    address = AddressSerializer(read_only=True)

    class Meta:
        model = Invoice
        fields = (
            'id',
            'FactorNumber',
            'products',
            'address_json',
            'address',
            'created_datetime',
            # 'final_invoice_price', # TODO : Field name `final_invoice_price` is not valid for model `Invoice`
            # 'final_coupon_price',  # TODO : Field name `final_coupon_price` is not valid for model `Invoice`
            # 'final_logistic_price', # TODO : Field name `final_logistic_price` is not valid for model `Invoice`
            'status',
            'receiver_name',
            'receiver_mobile')


class ProductLastStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'Price',
            'OldPrice',
            'Status',
            'PreparationDays',
            'Publish',
            'Title']


class ShopSlugSerializer(serializers.ModelSerializer):
    products = serializers.SerializerMethodField()

    class Meta:
        model = Shop
        fields = ('Slug', 'products')

    def get_products(self, obj):
        return obj.products


class UserImageSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = UserImage
        fields = ('id', 'image', 'title', 'description')


class ShopStatisticSerializer(serializers.ModelSerializer):
    products_count = serializers.SerializerMethodField()
    register_datetime = serializers.SerializerMethodField()
    total_sell = serializers.SerializerMethodField()
    mobile_number = serializers.SerializerMethodField()

    class Meta:
        model = Shop
        fields = ['ID', 'Title', 'Slug', 'products_count',
                  'register_datetime', 'total_sell', 'mobile_number']

    def get_products_count(self, obj):
        return obj.products_count

    def get_register_datetime(self, obj):
        return obj.DateCreate.strftime('%Y-%m-%d')

    def get_total_sell(self, obj):
        return obj.total_sell

    def get_mobile_number(self, obj):
        if obj.FK_ShopManager and hasattr(obj.FK_ShopManager, 'User_Profile'):
            return obj.FK_ShopManager.User_Profile.MobileNumber
        return None


class CampaignShopSerializer(serializers.ModelSerializer):
    products = serializers.SerializerMethodField()

    class Meta:
        model = Shop
        fields = ['ID', 'Title', 'Slug', 'products']

    def get_products(self, obj):
        products = obj.ShopProduct.order_by('?')[:2]
        return ProductListSerializer(products, many=True).data
