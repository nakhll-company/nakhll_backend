from __future__ import unicode_literals
import os
from functools import cached_property
import datetime
import math
import uuid
import random
import string
import os
from django.http import Http404
from django.db import models
from django.db.models import F, Q, Count, UniqueConstraint, CheckConstraint
from django.db.models.fields import FloatField
from django.db.models.functions import Cast
from django.db.models.aggregates import Avg, Sum
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.core import serializers
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils import timezone
from django.utils.deconstruct import deconstructible
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import reverse, get_object_or_404
from django_jalali.db import models as jmodels
from django.dispatch import receiver
from colorfield.fields import ColorField
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill
from simple_history.models import HistoricalRecords
from nakhll_market.interface import AlertInterface
from nakhll.utils import datetime2jalali

OUTOFSTOCK_LIMIT_NUM = 5


def attach_domain(url):
    domain = settings.DOMAIN_NAME
    # Cut domain trailing slash
    domain = domain if domain[-1] != '/' else domain[:-1]
    return domain + url


# Rename Method
@deconstructible
class PathAndRename():
    def __init__(self, sub_path):
        self.path = sub_path

    def __call__(self, instance, filename):
        ext = filename.split('.')[-1]
        rand_strings = ''.join(random.choice(
            string.ascii_letters + string.digits)
            for i in range(6))
        filename = '{}.{}'.format(rand_strings, ext)

        return os.path.join(self.path, filename)


# Random Referense Code
@deconstructible
class BuildReferenceCode():
    def __init__(self, Code_Size):
        self.size = Code_Size

    def __call__(self):
        random_str = ''.join(
            random.choice(string.ascii_lowercase + string.digits)
            for i in range(self.size))

        return (random_str)


# Fix Image Roting
def upload_path(instance, filename):
    return '{0}/{1}'.format("disforum", filename)


class CategoryManager(models.Manager):
    def available_category(self):
        queryset = self.get_queryset()
        return queryset.filter(available=True)

    def all_childs(self, category):
        childs = []
        for child in category.get_sub_category():
            childs.append(child)
            childs.extend(self.all_childs(child))
        return childs

    def parents_to_root(self, category):
        if category.parent is None:
            return [category]
        else:
            return self.parents_to_root(category.parent) + [category]

    def get_root_categories(self):
        return self.available_category().filter(parent=None).order_by('order')

    def categories_with_product_count(self, query=None, shop=None):
        filter_query = Q()
        if query:
            filter_query &= Q(products__Title__contains=query)
            filter_query &= Q(products__Publish=True)
            filter_query &= Q(products__FK_Shop__isnull=False)
        if shop:
            filter_query &= Q(products__FK_Shop__Slug=shop)

        queryset = self.annotate(
            products_count=Count(
                'products',
                filter=filter_query))
        return queryset.filter(products_count__gt=0).order_by('-products_count')

    def all_subcategories(self, categories):
        subcategories = []
        for category in categories:
            subcategories.append(category)
            subcategories.extend(
                self.all_subcategories(
                    category.childrens.all()))
        return subcategories

    def all_ordered(self):
        return self.available_category().order_by('order')


class Category(models.Model):
    class Meta:
        verbose_name = "???????? ????????"
        verbose_name_plural = "???????? ???????? ????"

    name = models.CharField(verbose_name='?????????? ???????? ????????', max_length=150)
    slug = models.SlugField(
        verbose_name='?????????? ???????? ????????',
        unique=True,
        db_index=True)
    description = models.TextField(verbose_name='???????????? ???????? ????????', blank=True)
    image = models.ImageField(
        verbose_name='?????? ???????? ????????',
        upload_to=PathAndRename('media/Pictures/Categories/'),
        help_text='?????? ???????? ???????? ???? ?????????? ???????? ????????',
        blank=True,
        null=True)
    image_thumbnail = ImageSpecField(source='image',
                                     processors=[ResizeToFill(175, 175)],
                                     format='JPEG',
                                     options={'quality': 60})
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        verbose_name='??????',
        blank=True,
        null=True,
        related_name='childrens')
    available = models.BooleanField(verbose_name='????????', default=True)
    created_at = models.DateTimeField(
        verbose_name='?????????? ??????????', auto_now_add=True)
    updated_at = models.DateTimeField(
        verbose_name='?????????? ??????????????????', auto_now=True)
    market_uuid = models.UUIDField(
        verbose_name='?????????? ??????????',
        null=True,
        editable=False)
    submarket_uuid = models.UUIDField(
        verbose_name='?????????? ??????????????',
        null=True,
        editable=False)
    order = models.PositiveIntegerField(verbose_name='??????????', default=99999)
    objects = CategoryManager()

    def __str__(self):
        return "{}".format(self.name)


# ----------------------------------------------------------------------------------------------------------------------------------

class ShopManager(models.Manager):
    FEW_HOURS_AGO = timezone.make_aware(
        datetime.datetime.now() -
        datetime.timedelta(
            hours=15))

    def shop_managers_info(self):
        queryset = self.get_queryset()
        return queryset.values(
            'FK_ShopManager__first_name',
            'FK_ShopManager__last_name',
            'FK_ShopManager__User_Profile__NationalCode',
            'State',
            'BigCity',
            'City',
            'Location',
        )

    def shop_managers_info_marketing(self):
        queryset = self.get_queryset()
        return queryset.values(
            'FK_ShopManager__first_name',
            'FK_ShopManager__last_name',
            'FK_ShopManager__User_Profile__MobileNumber',
            'State',
            'BigCity',
            'City',
            'Location',
        )

    def most_last_week_sale_shops(self):
        queryset = self.get_queryset()
        number_of_days = 7
        now = timezone.now()
        one_week_ago = now - datetime.timedelta(days=7)

        # Exclude the ones that have been created less than 15 Hours ago
        # Exclude Shops that have default Image
        return queryset .filter(Q(Publish=True), Q(Available=True), Q(DateCreate__lt=self.FEW_HOURS_AGO), Q(ShopProduct__Factor_Product__Factor_Products__OrderDate__gte=one_week_ago), ~Q(
            Image='static/Pictures/DefaultShop.png')) .annotate(number_sale=Sum('ShopProduct__Factor_Product__ProductCount')) .order_by('-number_sale')[:5]

    def get_random_shops(self):
        # Shop.objects\
        # .filter(Publish = True, Available = True)\
        # .annotate(product_count = Count('ShopProduct'))\
        # .filter(product_count__gt=1)\
        # .order_by('?')[:12]
        sql = '''
            SELECT
                "nakhll_market_shop"."ID",
                "nakhll_market_shop"."FK_ShopManager_id",
                "nakhll_market_shop"."Title",
                "nakhll_market_shop"."Slug",
                "nakhll_market_shop"."Description",
                "nakhll_market_shop"."Image",
                "nakhll_market_shop"."NewImage",
                "nakhll_market_shop"."ColorCode",
                "nakhll_market_shop"."Bio",
                "nakhll_market_shop"."State",
                "nakhll_market_shop"."BigCity",
                "nakhll_market_shop"."City",
                "nakhll_market_shop"."Location",
                "nakhll_market_shop"."Point",
                "nakhll_market_shop"."Holidays",
                "nakhll_market_shop"."DateCreate",
                "nakhll_market_shop"."DateUpdate",
                "nakhll_market_shop"."Edite",
                "nakhll_market_shop"."Available",
                "nakhll_market_shop"."Publish",
                "nakhll_market_shop"."FK_User_id",
                "nakhll_market_shop"."CanselCount",
                "nakhll_market_shop"."CanselFirstDate",
                "nakhll_market_shop"."LimitCancellationDate",
                "nakhll_market_shop"."documents",
                COUNT("nakhll_market_product"."ID") AS "product_count"
            FROM "nakhll_market_shop"
            LEFT OUTER JOIN
                "nakhll_market_product" ON ("nakhll_market_shop"."ID" = "nakhll_market_product"."FK_Shop_id")
            WHERE ("nakhll_market_shop"."Available" AND "nakhll_market_shop"."Publish"
                    AND "nakhll_market_shop"."DateCreate" > now() - '15 hours'::INTERVAL)
            GROUP BY "nakhll_market_shop"."ID"
            HAVING COUNT("nakhll_market_product"."ID") > 1
            ORDER BY RANDOM()
            LIMIT 12
        '''
        # METHOD A:
        # return Shop.objects.raw(sql)

        # METHOD B:
        # shops = Shop.objects.filter(Publish=True, Available=True, ShopProduct__gt=1, DateCreate__lt=self.FEW_HOURS_AGO).order_by('?')[:12]

        # METHOD C:

        # METHOD D:
        shop_ids = Shop.objects.filter(Q(Publish=True), Q(Available=True), Q(ShopProduct__gt=1),
                                       # Exclude the ones that have been created
                                       # less than 15 Hours ago
                                       Q(DateCreate__lt=self.FEW_HOURS_AGO),
                                       # Exclude Shops that have default Image
                                       ~Q(Image='static/Pictures/DefaultShop.png')).values_list('ID', flat=True)
        random_id_list = random.sample(list(shop_ids), 12)
        shops = Shop.objects.filter(ID__in=random_id_list)
        return shops

    def public_shops(self):
        return self.filter(Publish=True, Available=True)


# Shop (????????) Model
class Shop(models.Model):
    objects = ShopManager()
    ID = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True)
    FK_ShopManager = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name='???????? ??????',
        related_name='ShopManager')
    Title = models.CharField(
        max_length=100,
        verbose_name='?????????? ????????',
        db_index=True,
        unique=True)
    Slug = models.SlugField(
        verbose_name='?????????? ????????',
        unique=True,
        db_index=True,
        allow_unicode=True)
    Description = models.TextField(verbose_name='???????????? ????????', blank=True)
    Image = models.ImageField(
        verbose_name='?????? ????????',
        upload_to=PathAndRename('media/Pictures/Markets/SubMarkets/Shops/'),
        help_text='?????? ???????? ???? ?????????? ???????? ????????',
        default='static/Pictures/DefaultShop.png', null=True)
    Image_thumbnail = ImageSpecField(source='Image',
                                     processors=[ResizeToFill(175, 175)],
                                     format='JPEG',
                                     options={'quality': 60})
    NewImage = models.ImageField(
        verbose_name='?????? ???????? ????????',
        upload_to=PathAndRename('media/Pictures/Markets/SubMarkets/Shops/'),
        null=True, blank=True)
    ColorCode = models.CharField(
        max_length=9, verbose_name='???? ??????',
        help_text='?????? ???????? ???? ?????????? ???????? ????????', blank=True)
    Bio = models.TextField(verbose_name='?????????? ???????? ??????', blank=True)
    # these are only for backup purposes
    state_old = models.CharField(
        max_length=50,
        blank=True)
    big_city_old = models.CharField(
        max_length=50,
        blank=True)
    city_old = models.CharField(max_length=50, blank=True)
    State = models.ForeignKey(
        'State',
        on_delete=models.PROTECT,
        verbose_name='??????????',
        blank=True,
        null=True)
    BigCity = models.ForeignKey(
        'BigCity',
        on_delete=models.PROTECT,
        verbose_name='??????????????',
        blank=True,
        null=True)
    City = models.ForeignKey(
        'City',
        on_delete=models.PROTECT,
        verbose_name='??????',
        blank=True,
        null=True)
    Location = models.CharField(
        verbose_name='???????????? ??????????',
        max_length=150,
        blank=True,
        help_text='?????? ?? ?????? ??????????????????')
    Point = models.PositiveIntegerField(verbose_name='???????????? ????????', default=0)
    Holidays = models.CharField(
        verbose_name='?????? ?????? ???????????? ????????',
        max_length=15,
        blank=True)
    DateCreate = models.DateTimeField(
        verbose_name='?????????? ?????? ????????',
        auto_now_add=True)
    DateUpdate = models.DateTimeField(
        verbose_name='?????????? ?????????????????? ????????', auto_now=True)
    in_campaign = models.BooleanField(verbose_name='???? ????????????', default=False)
    # ?????????????? ?????? ????????
    AVAILABLE_STATUS = (
        (True, '????????'),
        (False, '?????? ????????'),
    )
    PUBLISH_STATUS = (
        (True, '?????????? ??????'),
        (False, '???? ???????????? ??????????'),
    )
    EDITE_STATUS = (
        (True, '???? ?????? ?????????? ??????????????'),
        (False, '???????????? ?????????? ?????? ??????'),
    )
    Edite = models.BooleanField(
        verbose_name='?????????? ???????????? ????????',
        choices=EDITE_STATUS,
        default=False)
    Available = models.BooleanField(
        verbose_name='?????????? ?????? ????????',
        choices=AVAILABLE_STATUS,
        default=True)
    Publish = models.BooleanField(
        verbose_name='?????????? ???????????? ????????',
        choices=PUBLISH_STATUS,
        default=False)
    FK_User = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        verbose_name='?????????? ??????????',
        related_name='Shop_Accept',
        blank=True,
        null=True)
    CanselCount = models.PositiveIntegerField(
        verbose_name='?????????? ?????? ?????????????? ????????', default=0)
    CanselFirstDate = models.DateField(
        verbose_name='?????????? ?????????? ?????? ??????????', null=True, blank=True)
    LimitCancellationDate = models.DateField(
        verbose_name='?????????? ?????????????? ?????? ??????????????', null=True, blank=True)
    documents = ArrayField(
        base_field=models.ImageField(
            verbose_name='?????? ???????? ????????',
            upload_to=PathAndRename('media/Pictures/Shop/Document/'),
            null=True,
            blank=True
        ),
        default=list,
        blank=True,
    )
    show_contact_info = models.BooleanField(
        '?????????? ?????????????? ???????? ????????', default=False)
    is_landing = models.BooleanField(
        verbose_name='???????? ???????? ???????????? ????????', default=False)
    has_product_group_add_edit_permission = models.BooleanField(
        verbose_name='???????? ???????????? ?????????? ?? ???????????? ?????????? ???? ???????? ?????????? ???? ?????????????? ???? ???????? ??????????',
        default=False)

    def __str__(self):
        return "{}".format(self.Title)

    @property
    def id(self):
        return self.ID

    @property
    def slug(self):
        return self.Slug

    @property
    def title(self):
        return self.Title

    @property
    def point(self):
        return self.Point

    @property
    def publish(self):
        return self.Publish

    @property
    def available(self):
        return self.Available

    @property
    def state(self):
        return self.State

    @property
    def big_city(self):
        return self.BigCity

    @property
    def city(self):
        return self.City

    @property
    def url(self):
        return self.get_absolute_url

    @property
    def description(self):
        return self.Description

    @property
    def image_thumbnail_url(self):
        return self.Image_thumbnail_url

    @property
    def profile(self):
        if self.FK_ShopManager:
            return self.FK_ShopManager.User_Profile
        return None

    @property
    def products(self):
        return self.ShopProduct.all()

    @property
    def url(self):
        return self.get_absolute_url

    @property
    def image_thumbnail_url(self):
        return self.Image_thumbnail_url

    @property
    def products_count(self):
        return self.get_products().count()

    @property
    def date_created(self):
        return datetime2jalali(self.DateCreate)

    @property
    def date_updated(self):
        return datetime2jalali(self.DateUpdate)

    @property
    def total_sell(self):
        return self.invoice_model.objects.shop_total_sell_amount(self)

    @property
    def last_sell_date(self):
        return self.invoice_model.objects.shop_last_sell_date(self)

    @property
    def manager_last_login(self):
        return datetime2jalali(self.FK_ShopManager.last_login)

    @property
    def manager_mobile_number(self):
        if self.FK_ShopManager and hasattr(self.FK_ShopManager, 'User_Profile'):
            return self.FK_ShopManager.User_Profile.MobileNumber
        return None

    @property
    def manager_full_name(self):
        manager = self.FK_ShopManager
        return f'{manager.first_name} {manager.last_name}'

    @cached_property
    def invoice_model(self):
        from invoice.models import Invoice
        return Invoice

    def get_absolute_url(self):
        return attach_domain(f'/shop/{self.Slug}/')

    def Image_thumbnail_url(self):
        try:
            i = self.Image_thumbnail.url
            url = self.Image_thumbnail.url
            return attach_domain(url)
        except BaseException:
            url = "https://nakhll.com/media/Pictures/default.jpg"
            return url

    def get_holidays(self):
        return self.Holidays.split('-')

    def get_products_category(self):
        category = []
        for item in self.get_products():
            for category_item in item.FK_Category.filter(
                    FK_SubCategory=None, Publish=True):
                category.append(category_item)
        category = list(dict.fromkeys(category))
        return category

    def is_available(self):
        return self.Available and self.Publish

    def __str__(self):
        return "{}".format(self.Title)

    def Image_thumbnail_url(self):
        try:
            i = self.Image_thumbnail.url
            url = self.Image_thumbnail.url
            return attach_domain(url)
        except BaseException:
            url = "https://nakhll.com/media/Pictures/default.jpg"
            return url

    def get_holidays(self):
        return self.Holidays.split('-')

    def get_products_category(self):
        category = []
        for item in self.get_products():
            for category_item in item.FK_Category.filter(
                    FK_SubCategory=None, Publish=True):
                category.append(category_item)
        category = list(dict.fromkeys(category))
        return category

    def get_products(self):
        return self.ShopProduct.filter(
            Publish=True)

    def get_all_products(self):
        return self.ShopProduct.all()

    def get_all_products_for_view(self):
        this_shop_product = list(
            Product.objects.filter(
                FK_Shop=self,
                Available=True,
                Publish=True,
                Status__in=[
                    '1',
                    '2',
                    '3']).order_by('-DateCreate'))
        this_shop_product += list(
            Product.objects.filter(
                FK_Shop=self,
                Available=True,
                Publish=True,
                Status='4').order_by('-DateCreate'))
        return this_shop_product

    def get_comments(self):
        raise NotImplementedError()

    def get_managment_image(self):
        return Profile.objects.get(
            FK_User=self.FK_ShopManager).Image_thumbnail_url()

    def get_shop_manager_full_name(self):
        return '{} {}'.format(self.FK_ShopManager.first_name,
                              self.FK_ShopManager.last_name)

    def get_active_landing(self):
        return self.landings.filter(
            status=shop_models.ShopLanding.Statuses.ACTIVE).first()

    def has_advertisement(self):
        if hasattr(self, 'advertisement'):
            return self.advertisement.yektanet_status == self.advertisement.YektanetStatuses.ACTIVE
        return False

    def get_advertisement(self):
        if self.has_advertisement():
            return self.advertisement
        return None

    def delete_image(self) -> None:
        """ Delete image

        This method delete image from storage and set image to Default image
        """
        if self.Image:
            self.Image.delete()
        self.save()

    class Meta:
        ordering = ('DateCreate', 'Title',)
        verbose_name = "????????"
        verbose_name_plural = "???????? ????"


class ShopSocialMedia(models.Model):
    class Meta:
        verbose_name = '???????? ?????????????? ????????'
        verbose_name_plural = '????????????????? ?????????????? ????????'

    def __str__(self):
        if hasattr(self, 'shop'):
            return self.shop.Slug
        return self.id

    shop = models.OneToOneField(
        Shop,
        verbose_name='????????',
        on_delete=models.CASCADE,
        related_name='social_media')
    telegram = models.CharField(
        '????????????',
        max_length=100,
        help_text='??????????? ???????????? ???????? ?????? ????????',
        null=True,
        blank=True)
    instagram = models.CharField(
        '????????????????????',
        max_length=100,
        help_text='??????????? ???????????????????? ???????? ?????? ????????',
        null=True,
        blank=True)


# ----------------------------------------------------------------------------------------------------------------------------------
# ShopBankAccount (????????????????? ????????) Model

def iban_validator(value):
    if not value.isdigit():
        raise ValidationError(_(f'?????????? {value} ???????? ?????? ?????? ????????'))
    if len(value) != 24:
        raise ValidationError(_(f'?????????? {value} ???????? ?????? 24 ?????? ????????'))


class ShopBankAccount(models.Model):
    class Meta:
        verbose_name = '???????? ?????????? ????????'
        verbose_name_plural = '????????????????? ????????'

    def __str__(self):
        if hasattr(self, 'shop'):
            return self.shop.Slug
        return self.id

    shop = models.OneToOneField(
        Shop,
        verbose_name='????????',
        on_delete=models.CASCADE,
        related_name='bank_account')
    iban = models.CharField(
        '?????????? ??????',
        max_length=24,
        help_text='?????????? ?????? ???????? IR',
        null=True,
        blank=True,
        validators=[iban_validator])
    owner = models.CharField('???????? ????????', max_length=100, null=True, blank=True)


class ProductManager(models.Manager):
    FEW_HOURS_AGO = timezone.make_aware(
        datetime.datetime.now() -
        datetime.timedelta(
            hours=15))

    def get_most_discount_precentage_available_product(self):
        queryset = self.get_queryset()
        return queryset.filter(
            Publish=True, Available=True, Status__in=['1', '2', '3'],
            DateCreate__lt=self.FEW_HOURS_AGO).exclude(
            OldPrice=0).annotate(
            OldPrice_float=Cast(F('OldPrice'),
                                FloatField())).annotate(
            Price_float=Cast(F('Price'),
                             FloatField())).annotate(
            discount_ratio=(F('OldPrice_float') - F('Price_float')) /
            F('OldPrice_float')).order_by('-discount_ratio')

    def get_one_most_discount_precenetage_available_product_random(self):
        result = self.get_most_discount_precentage_available_product()
        random_id = random.randint(0, int(result.count() / 10))
        return result[random_id]

    def get_last_created_products(self):
        return Product.objects \
            .filter(Publish=True, Available=True, OldPrice=0, Status__in=['1', '2', '3'],
                    DateCreate__lt=self.FEW_HOURS_AGO) \
            .order_by('-DateCreate')[:12]

    def get_last_created_discounted_products(self):
        return Product.objects.filter(
            Publish=True, Available=True, Status__in=['1', '2', '3'],
            DateCreate__lt=self.FEW_HOURS_AGO).exclude(
            OldPrice=0).order_by('-DateCreate')[
            : 16]

    def available_products(self):
        return self.filter(
            Publish=True,
            Available=True,
            FK_Shop__Available=True,
            FK_Shop__Publish=True)

    def get_random_products(self):
        return self.available_products().filter(
            OldPrice=0,
            Status__in=['1', '2', '3'],
            DateCreate__lt=self.FEW_HOURS_AGO
        ).order_by('?')[:16]

    def get_most_discount_precentage_products(self):
        return self \
            .get_most_discount_precentage_available_product() \
            .order_by('?')[:15]

    def get_products_in_same_factor(self, id):
        queryset = self.get_queryset()
        try:
            product = Product.objects.get(ID=id)
            return Product.objects.filter(
                Factor_Product__Factor_Products__FK_FactorPost__FK_Product=product,
                DateCreated__lt=self.FEW_HOURS_AGO).exclude(
                ID=product.ID).distinct()
        except BaseException:
            return None

    def get_user_shop_products(self, user, shop, order=None):
        queryset = self.get_queryset()
        if order and order in ['total_sell', 'title']:
            try:
                products = self.filter(
                    FK_Shop=shop,
                    FK_Shop__FK_ShopManager=user,
                    Publish=True)
                if order == 'total_sell':
                    return products.annotate(
                        num=Count('Factor_Product')).order_by('-num')
                elif order == 'title':
                    return products.order_by('Title')
            except BaseException:
                pass
        return self.filter(FK_Shop=shop, FK_Shop__FK_ShopManager=user)

    def user_shop_active_products(self, user, shop_slug):
        return self.filter(
            FK_Shop__FK_ShopManager=user, FK_Shop__Slug=shop_slug,
            Available=True, Publish=True)

    def user_shop_inactive_products(self, user, shop_slug):
        return self.filter(
            FK_Shop__FK_ShopManager=user, FK_Shop__Slug=shop_slug,
            Available=False, Publish=True)

    def nearly_outofstock_products(self, user, shop_slug):
        return self.filter(FK_Shop__FK_ShopManager=user,
                           FK_Shop__Slug=shop_slug, Publish=True,
                           Inventory__lt=OUTOFSTOCK_LIMIT_NUM)

    def outofstock_products(self, user, shop_slug):
        return self.filter(FK_Shop__FK_ShopManager=user,
                           FK_Shop__Slug=shop_slug, Publish=True,
                           Inventory__lt=1)

    @staticmethod
    def is_product_available(product, count):
        ''' Check if product is available and published and also have enough items in stock '''
        return product.Available and product.Publish and product.Status != '4'

    @staticmethod
    def has_enough_items_in_stock(product, count):
        ''' Check if product have enough items in stock '''
        return (product.Status == '1' and product.inventory >= count) \
            or (product.Status in ['2', '3'])

    def is_product_list_valid(self, product_list):
        ''' Check if products in product_list is available, published and have enough in stock
            Optimization is important here. What I do now is first check for availability and
            being published all in one query; so if a product is not avaiable or published, it
            rejects the product_list and return False. However if this step is passed, it will
            check every product count one by one.
            Maybe it could be better if I check for product availability and being published
            and product count one by one. I don't know...
        '''
        product_ids = [x.get('product').id for x in product_list]
        if self.filter(
                Q(ID__in=product_ids) and (
                    Q(Available=False) or Q(Publish=False)
                )).exists():
            return False
        for item in product_list:
            product = item.get('product').get_from_db()
            if product.Inventory < item.get('count'):
                return False
        return True

    @staticmethod
    def jsonify_product(product):
        if isinstance(product, Product):
            product = [product]
        return serializers.serialize('json', product, ensure_ascii=False)

    def all_public_products(self):
        return self.filter(Publish=True, Available=True).order_by('-DateUpdate')

    def get_available_products(self):
        return self.get_queryset().filter(
            Publish=True, Available=True, Status__in=['1', '2', '3'],
            Inventory=True, FK_Shop__Available=True, FK_Shop__Publish=True)

    def get_most_sold_product(self):
        return self.get_available_products() \
                   .annotate(num_sell=Count('invoice_items__invoice')) \
                   .order_by('-num_sell')[:20]

    @staticmethod
    def get_product(id, raise_exception=True):
        try:
            return Product.objects.get(ID=id)
        except BaseException:
            if raise_exception:
                raise Http404
            return None


# Product (??????????) Model
class Product(models.Model):
    POSTRANGE_TYPE = (
        ('1', '?????????? ????????'),
        ('2', '????????????'),
        ('3', '????????????????'),
        ('4', '????????'),
    )
    PRODUCT_STATUS = (
        ('1', '?????????? ???? ??????????'),
        ('2', '?????????? ?????? ???? ??????????'),
        ('3', '???????????? ???????? ????????'),
        ('4', '?????????? ????????'),
    )
    AVAILABLE_STATUS = (
        (True, '????????'),
        (False, '?????? ????????'),
    )
    PUBLISH_STATUS = (
        (True, '?????????? ??????'),
        (False, '???? ???????????? ??????????'),
    )
    EDITE_STATUS = (
        (True, '???? ?????? ?????????? ??????????????'),
        (False, '???????????? ?????????? ?????? ??????'),
    )
    objects = ProductManager()
    ID = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True)
    Title = models.CharField(
        max_length=200,
        verbose_name='?????? ??????????',
        db_index=True)
    Slug = models.SlugField(
        max_length=200,
        verbose_name='?????????? ??????????',
        unique=True,
        db_index=True,
        allow_unicode=True)
    Story = models.TextField(verbose_name='???????????? ??????????', blank=True)
    Description = models.TextField(verbose_name='???????????? ??????????', blank=True)
    Bio = models.TextField(verbose_name='?????????? ??????????', blank=True)
    Image = models.ImageField(
        verbose_name='?????? ??????????',
        upload_to=PathAndRename(
            'media/Pictures/Markets/SubMarkets/Shops/Products/'),
        help_text='?????? ?????????? ?????? ???? ?????????? ???????????????? ????????')
    Image_thumbnail = ImageSpecField(source='Image',
                                     processors=[ResizeToFill(180, 180)],
                                     format='JPEG',
                                     options={'quality': 60})
    Image_medium = ImageSpecField(source='Image',
                                  processors=[ResizeToFill(450, 450)],
                                  format='JPEG',
                                  options={'quality': 60})
    NewImage = models.ImageField(
        verbose_name='?????? ???????? ????????',
        upload_to=PathAndRename(
            'media/Pictures/Markets/SubMarkets/Shops/Products/'),
        null=True, blank=True)
    Catalog = models.FileField(
        verbose_name='?????????????? ??????????',
        upload_to=PathAndRename(
            'media/Catalogs/Markets/SubMarkets/Shops/Products/'),
        help_text='?????????????? ?????????? ?????? ???? ?????????? ???????? ????????', null=True, blank=True)
    FK_Shop = models.ForeignKey(
        Shop,
        on_delete=models.PROTECT,
        verbose_name='????????',
        related_name='ShopProduct')
    category = models.ForeignKey(
        Category,
        verbose_name='???????? ???????? ????????',
        related_name='products',
        on_delete=models.PROTECT,
        db_column='category_id')
    Price = models.BigIntegerField(verbose_name='???????? ??????????')
    OldPrice = models.BigIntegerField(verbose_name='???????? ?????? ??????????', default=0)
    # Product Weight Info
    Net_Weight = models.CharField(
        verbose_name='?????? ???????? ?????????? (??????)',
        max_length=6,
        default='0')
    Weight_With_Packing = models.CharField(
        verbose_name='?????? ?????????? ???? ???????? ???????? (??????)',
        max_length=6,
        default='0')
    # Product Dimensions Info
    Length_With_Packaging = models.CharField(
        verbose_name='?????? ?????????? ???? ???????? ???????? (?????????? ??????(', max_length=4, default='0')
    Width_With_Packaging = models.CharField(
        verbose_name='?????? ?????????? ???? ???????? ???????? (?????????? ??????(', max_length=4, default='0')
    Height_With_Packaging = models.CharField(
        verbose_name='???????????? ?????????? ???? ???????? ???????? (?????????? ??????(', max_length=4, default='0')
    # Product Inventory
    Inventory = models.PositiveIntegerField(
        verbose_name='?????????? ???????????? ???? ?????? ???????? ???? ??????????', default=5)

    PostRangeType = models.CharField(
        verbose_name='???????????? ?????????? ??????????????', max_length=1,
        choices=POSTRANGE_TYPE, default='1',
        help_text='???????????? ?????????? ???? ???? ???????? ???????? ?????? ???????? ???????? ?????????? ????????.')

    Status = models.CharField(
        verbose_name='?????????? ????????',
        max_length=1,
        choices=PRODUCT_STATUS)
    DateCreate = models.DateTimeField(
        verbose_name='?????????? ???????????????? ??????????',
        auto_now_add=True)
    DateUpdate = models.DateTimeField(
        verbose_name='?????????? ?????????????????? ??????????', auto_now=True)

    Edite = models.BooleanField(
        verbose_name='?????????? ???????????? ??????????',
        choices=EDITE_STATUS,
        default=False)
    Available = models.BooleanField(
        verbose_name='?????????? ???????????????? ??????????',
        choices=AVAILABLE_STATUS,
        default=True)
    Publish = models.BooleanField(
        verbose_name='?????????? ???????????? ??????????',
        choices=PUBLISH_STATUS,
        default=True)
    FK_User = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        verbose_name='?????????? ??????????',
        related_name='Product_Accept',
        blank=True,
        null=True)
    PreparationDays = models.PositiveSmallIntegerField(
        verbose_name='???????? ?????????????????????', null=True)
    post_range_cities = models.ManyToManyField(
        'City',
        related_name='products',
        verbose_name=_('???????????? ???????? ??????????'),
        blank=True)
    is_advertisement = models.BooleanField(
        verbose_name=_('????????'), default=False, null=True)
    barcode = models.CharField(
        verbose_name='??????????',
        max_length=13,
        null=True,
        blank=True)
    aparat_video_script = models.CharField(
        verbose_name='?????????????? ?????????? ????????????', 
        max_length=255,
        null=True,
        blank=True,
        default=None)
    history = HistoricalRecords()

    @property
    def id(self):
        return self.ID

    @property
    def user(self):
        return self.FK_User

    @property
    def image(self):
        return self.get_image()

    @property
    def description(self):
        return self.Description

    @property
    def available(self):
        return self.Available

    @property
    def publish(self):
        return self.Publish

    @property
    def old_price(self):
        return self.OldPrice

    @old_price.setter
    def old_price(self, value):
        self.OldPrice = value

    @property
    def price(self):
        return self.Price

    @price.setter
    def price(self, value):
        self.Price = value

    @property
    def slug(self):
        return self.Slug

    @property
    def title(self):
        return self.Title

    @property
    def status(self):
        return self.get_status()

    @property
    def id(self):
        return self.ID

    @property
    def net_weight(self):
        return self.Net_Weight

    @property
    def weight_with_packing(self):
        return self.Weight_With_Packing

    @property
    def length_with_packing(self):
        return self.Length_With_Packaging

    @property
    def width_with_packing(self):
        return self.Width_With_Packaging

    @property
    def height_with_packaging(self):
        return self.Height_With_Packaging

    @property
    def story(self):
        return self.Story

    @property
    def post_range(self):
        return self.FK_PostRange.all()

    @property
    def exception_post_range(self):
        return self.FK_ExceptionPostRange.all()

    @property
    def image_thumbnail_url(self):
        return self.Image_thumbnail_url()

    @property
    def url(self):
        return self.get_url()

    @property
    def discount(self):
        return self.get_discounted()

    @property
    def related_products(self):
        return self.get_related_products()

    @property
    def attributes(self):
        return self.Product_Attr.all()

    @property
    def attributes_price(self):
        return self.AttrPrice_Product.all()

    @property
    def banners(self):
        return self.Product_Banner.all()

    @property
    def reviews(self):
        return self.Product_Review.all()

    @property
    def comments_count(self):
        return self.Product_Comment.count()

    @property
    def comments(self):
        return self.Product_Comment.filter(FK_Pater=None)

    @property
    def shop(self):
        return self.FK_Shop

    @property
    def inventory(self):
        return self.Inventory

    @property
    def average_user_point(self):
        return self.FK_Points.aggregate(average=Avg('Point'))['average']

    @property
    def total_sell(self):
        return self.Factor_Product.count()

    @property
    def preparation_days(self):
        return self.PreparationDays

    @property
    def post_range_type(self):
        return self.PostRangeType

    def is_available(self):
        return self.Available and self.Publish and self.FK_Shop.is_available()

    @property
    def salable(self):
        return self.is_available()

    def has_enough_items_in_stock(self, count):
        ''' Check if product have enough items in stock '''
        return (self.Status == '1' and self.inventory >= count) \
            or (self.Status in ['2', '3'])

    # These properties are created for Torob API
    @property
    def page_url(self):
        url = f'/torob/products/{self.ID}/'
        return attach_domain(url)

    @property
    def page_unique(self):
        return self.ID

    @property
    def subtitle(self):
        return self.Slug

    @property
    def current_price(self):
        return self.Price

    @property
    def availability(self):
        return 'instock' if self.Available and self.Publish and \
            self.FK_Shop.is_available() and \
            (self.Status == '1' and self.inventory) or \
            (self.Status in ['2', '3']) else ''

    @property
    def category_name(self):
        return self.category.name

    @property
    def image_link(self):
        if self.Image:
            return attach_domain(self.Image.url)

    @property
    def short_desc(self):
        return self.Description

    def __str__(self):
        return "{}".format(self.Title)

    def get_status(self):
        Status = {
            "1": '?????????? ???? ??????????',
            "2": '?????????? ?????? ???? ??????????',
            "3": '???????????? ???????? ????????',
            "4": '?????????? ????????',
        }
        return Status[self.Status] if (self.Status == '1' and self.inventory) \
            or (self.Status in ['2', '3']) else Status['4']

    def get_sendtype(self):
        SendType = {
            "1": '?????????? ????????',
            "2": '????????????',
            "3": '????????????????',
            "4": '????????',
        }
        return SendType[self.PostRangeType]

    def get_absolute_url(self):
        return attach_domain(f'/shop/{self.FK_Shop.Slug}/product/{self.Slug}')

    def get_add_to_cart_url(self):
        return reverse("Payment:add-to-cart", kwargs={
            'ID': self.ID
        })

    def get_remove_from_cart_url(self):
        return reverse("Payment:remove-from-cart", kwargs={
            'ID': self.ID
        })

    def get_discounted(self):
        # Get Discounted
        try:
            return int((self.OldPrice - self.Price) * 100 / self.OldPrice)
        except BaseException:
            return 0

    def get_product_net_weight(self):
        # Get Net Weight
        try:
            return self.Net_Weight
        except BaseException:
            return '???? ????????'

    def get_product_weight_with_packing(self):
        # Get Weight With Packing
        try:
            return self.Weight_With_Packing
        except BaseException:
            return '???? ????????'

    def get_product_dimensions(self):
        # Get Dimensions
        try:
            return str(self.Length_With_Packaging) + ' * ' + str(
                self.Width_With_Packaging) + ' * ' + str(self.Height_With_Packaging)
        except BaseException:
            return '???? ????????'

    def get_product_weight_convert_to_int(self):
        # Get Product Weightn Convert To Int
        try:
            net_weight = int(self.Net_Weight)
            weight_with_packing = int(self.Weight_With_Packing)
            this_sum = 0
            if (weight_with_packing > net_weight) or (
                    weight_with_packing == net_weight):
                this_sum += weight_with_packing
            else:
                this_sum += net_weight
            return this_sum
        except BaseException:
            return 0

    def get_product_packing_volume_convert_to_int(self):
        # Get Product Packing Volume Convert To Int
        try:
            vloume = int(self.Length_With_Packaging) * int(
                self.Width_With_Packaging) * int(self.Height_With_Packaging)
            this_vloume = 0
            if vloume > 3000:
                this_vloume += math.ceil(vloume / 3000) * 50
            elif vloume != 0:
                this_vloume += 50
            return this_vloume
        except BaseException:
            return 0

    def get_total_product_weight(self):
        try:
            return self.get_product_weight_convert_to_int(
            ) + self.get_product_packing_volume_convert_to_int()
        except BaseException:
            return 0

    def check_product_post_status(self):
        # Check Product Post Status
        if (self.get_total_product_weight() > 40000) or (
                (int(self.Length_With_Packaging) > 100) or (int(self.Width_With_Packaging) > 100) or (
                int(self.Height_With_Packaging) > 100)):
            return True
        else:
            return False

    def default_image_url(self):
        return 'https://nakhll.com/media/Pictures/default.jpg'

    def get_image(self):
        try:
            return attach_domain(self.Image.url)
        except BaseException:
            return self.default_image_url()

    def get_image_alt(self):
        return self.Title

    def Image_thumbnail_url(self):
        try:
            url = self.Image_thumbnail.url
            return attach_domain(url)
        except BaseException:
            url = "https://nakhll.com/media/Pictures/default.jpg"
            return url

    def Image_medium_url(self):
        try:
            url = self.Image_medium.url
            return attach_domain(url)
        except BaseException:
            url = "https://nakhll.com/media/Pictures/default.jpg"
            return url

    def get_url(self):
        try:
            return reverse("nakhll_market:ProductsDetail", kwargs={
                'shop_slug': self.FK_Shop.Slug,
                'product_slug': self.Slug
            })
        except BaseException:
            return '/'

    def get_point(self):
        try:
            this_point = 0.0
            for item in self.FK_Points.all():
                this_point += item.Point
            return round(this_point / self.get_point_count(), 2)
        except BaseException:
            return 0.0

    def Point(self):
        return self.get_point()

    def get_point_count(self):
        return self.FK_Points.all().count()

    def get_related_products(self):
        return Product.objects \
            .filter(
                Available=True,
                Publish=True,
                Status__in=['1', '2', '3'],
                FK_Category__in=self.FK_Category.all()
            ).order_by('?')[:12]

    def get_product_categories(self):
        raise NotImplementedError()

    def get_product_inpostrange(self):
        raise NotImplementedError()

    def get_product_outpostrange(self):
        raise NotImplementedError()

    def get_shop_slug(self):
        return self.FK_Shop.Slug

    def reduce_stock(self, count):
        ''' Reduce from inventory of this product '''
        if self.Inventory < count:
            AlertInterface.not_enogth_in_stock(self, count)
            return
        self.Inventory -= count
        self.save()

    class Meta:
        ordering = ('DateCreate', 'Title',)
        verbose_name = "??????????"
        verbose_name_plural = "??????????????"
        constraints = [
            UniqueConstraint(
                fields=[
                    'Title',
                    'FK_Shop_id'],
                name='unique_shop_product_title'),
            CheckConstraint(
                check=~Q(Price=0),
                name='check_price_not_zero'),
            CheckConstraint(
                check=Q(OldPrice__gt=F('Price')) | Q(OldPrice=0),
                name='price_is_greater_than_discounted_price'
            )]


class Tag(models.Model):
    """
    #TODO: Document
    """
    name = models.CharField(max_length=127, verbose_name=_('?????? ????'),
                            error_messages={
        'max_length': _('?????? ???? ???????? ???????? ???? 127 ?????????????? ????????.'), }
    )
    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        verbose_name=_('????????'),
        related_name="tags")

    class Meta:
        unique_together = ('name', 'shop')
        verbose_name = _('????')
        verbose_name_plural = _('???????')

    def __str__(self):
        return f"{self.name}"


class ProductTag(models.Model):
    """
        #TODO: Document
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        verbose_name=_('??????????'),
        related_name="product_tags")
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name=_('????'),
        related_name='product_tags')

    class Meta:
        unique_together = ('product', 'tag')
        verbose_name = _('???? ??????????')
        verbose_name_plural = _('???? ??????????')

    def __str__(self):
        return f"{self.product} - {self.tag}"


# Product Banner (?????????? ??????????) Model
class ProductBanner(models.Model):
    FK_Product = models.ForeignKey(
        Product,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name='?????? ??????????',
        related_name='Product_Banner')
    Title = models.CharField(
        verbose_name='?????????? ?????? ??????',
        max_length=100,
        null=True,
        blank=True,)
    Description = models.TextField(
        verbose_name='???????????? ??????',
        max_length=350,
        blank=True)
    URL = models.URLField(
        verbose_name='????????',
        help_text='?????????? ???? ???? ???????? ???????? ???? ???? ?????????? ???? ??????',
        blank=True)
    Image = models.ImageField(
        verbose_name='?????? ??????????',
        upload_to=PathAndRename(
            'media/Pictures/Markets/SubMarkets/Shops/Products/Banners/'),
        help_text='?????? ?????????? ???? ?????????? ???????? ????????')
    Image_medium = ImageSpecField(source='Image',
                                  processors=[ResizeToFill(450, 450)],
                                  format='JPEG',
                                  options={'quality': 60})
    NewImage = models.ImageField(
        verbose_name='?????? ???????? ????????',
        upload_to=PathAndRename(
            'media/Pictures/Markets/SubMarkets/Shops/Products/Banners/'),
        null=True, blank=True)
    BannerBuilder = models.CharField(
        verbose_name='?????? ?????????? ?????????? ??????',
        max_length=120,
        blank=True)
    BannerURL = models.URLField(verbose_name='???????? ?????????? ?????????? ??????', blank=True)
    DateCreate = models.DateTimeField(
        verbose_name='?????????? ???????????????? ?????? ??????????',
        auto_now_add=True)
    DateUpdate = models.DateTimeField(
        verbose_name='?????????? ?????????????????? ?????? ??????????', auto_now=True)
    AVAILABLE_STATUS = (
        (True, '????????'),
        (False, '?????? ????????'),
    )
    PUBLISH_STATUS = (
        (True, '?????????? ??????'),
        (False, '???? ???????????? ??????????'),
    )
    EDITE_STATUS = (
        (True, '???? ?????? ?????????? ??????????????'),
        (False, '???????????? ?????????? ?????? ??????'),
    )
    Edite = models.BooleanField(
        verbose_name='?????????? ???????????? ?????? ????????',
        choices=EDITE_STATUS,
        default=False)
    Available = models.BooleanField(
        verbose_name='?????????? ???????????????? ?????? ??????????',
        choices=AVAILABLE_STATUS,
        default=True)
    Publish = models.BooleanField(
        verbose_name='?????????? ???????????? ?????? ??????????',
        choices=PUBLISH_STATUS,
        default=False)
    FK_User = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        verbose_name='?????????? ??????????',
        related_name='Product_Banner_Accept',
        blank=True,
        null=True)

    @property
    def image(self):
        return self.Image_thumbnail_url()

    def Image_thumbnail_url(self):
        try:
            i = self.Image_medium.url
            url = self.Image_medium.url
            return attach_domain(url)
        except BaseException:
            url = "https://nakhll.com/media/Pictures/default.jpg"
            return url

    # Output Customization Based On Title
    def __str__(self):
        return "{}".format(self.Title)

    class Meta:
        ordering = ('id', 'Title',)
        verbose_name = "?????????? ??????????"
        verbose_name_plural = "?????????? ?????????????? "


# Comment (?????? ??????????) Model
class Comment(models.Model):
    TYPE_STATUS = (
        (False, '????????'),
        (True, '????????'),
    )
    Type = models.BooleanField(
        verbose_name='?????? ??????',
        choices=TYPE_STATUS,
        default=True)
    FK_UserAdder = models.ForeignKey(
        User, on_delete=models.SET_NULL, verbose_name='??????????',
        related_name='User_Comment', null=True)
    FK_Product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        verbose_name='??????????',
        related_name='Product_Comment',
        blank=True,
        null=True)
    Description = models.TextField(verbose_name='?????????????? ??????')
    FK_Like = models.ManyToManyField(
        User,
        verbose_name='???????? ??????????',
        related_name='Comment_Like',
        blank=True)
    FK_Pater = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        verbose_name='???????????? ??????',
        related_name='Comment_Pater',
        blank=True,
        null=True)
    Available = models.BooleanField(
        verbose_name='?????????? ???????????? ??????', default=False)
    DateCreate = models.DateTimeField(
        verbose_name='?????????? ?????? ??????',
        auto_now_add=True)
    FK_User = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        verbose_name='?????????? ??????????',
        related_name='Comment_Accept',
        blank=True,
        null=True)

    @property
    def user(self):
        return self.FK_UserAdder

    @property
    def product(self):
        return self.FK_Product

    @property
    def description(self):
        return self.Description

    @property
    def number_like(self):
        return self.FK_Like.count()

    @property
    def reply(self):
        return self.FK_Pater

    @property
    def date_create(self):
        return datetime2jalali(self.DateCreate)

    @property
    def type(self):
        return self.TYPE_STATUS[self.Type][1]

    def get_type(self):
        if self.Type:
            return '????????'
        else:
            return '????????'

    @property
    def comment_replies(self):
        if self.Comment_Pater:
            return self.Comment_Pater.all()

    def get_status(self):
        if self.Available:
            return '?????????? ??????'
        else:
            return '???? ?????? ??????????'

    def get_like_count(self):
        return self.FK_Like.all().count()

    def get_object_name(self):
        return '?????????? ' + self.FK_Product.Title

    # Output Customization Based On User Adder, Product
    def __str__(self):
        return "{} - {}".format(self.FK_UserAdder, self.FK_Product)

    # Ordering With DateCreate
    class Meta:
        ordering = ('id',)
        verbose_name = "?????? ??????????"
        verbose_name_plural = "?????????? ??????????????"

    # Get Comment Profile Image
    def get_comment_profile_image(self):
        try:
            # Get User Profile
            this_profile = get_object_or_404(Profile, FK_User=self.FK_UserAdder)
            return this_profile.Image_thumbnail_url()
        except BaseException:
            url = "https://nakhll.com/media/Pictures/avatar.png"
            return url


class ProfileQuerySet(models.QuerySet):
    def shop_count(self):
        return self.annotate(shop_count=Count('FK_User__ShopManager'))

    def have_shop(self):
        return self.filter(shop_count__gte=1)

    def have_not_shop(self):
        return self.filter(shop_count=0)


class ProfileManager(models.Manager):
    def get_queryset(self):
        return ProfileQuerySet(self.model, using=self._db)

    def get_user_by_mobile_number(self, mobile_number: str) -> User:
        queryset = self.get_queryset()
        return queryset.get(MobileNumber=mobile_number).FK_User

    def user_exists_by_mobile_number(self, mobile_number: str) -> bool:
        if self.get_user_by_mobile_number(mobile_number):
            return True
        else:
            return False

    def set_user_password_by_mobile_number(
            self, mobile_number, password) -> User:
        user = self.get_user_by_mobile_number(mobile_number)
        user.set_password(password)
        user.save()
        return user

    def create_profile(self, mobile_number, user, reference_code, user_ip):
        '''
        this function create user and all related objects
        it must be transactional because we create 3 objects
        or we don't need none of them.
        TODO MAKE IT TRANSACTIONAL
        '''
        queryset = self.get_queryset()
        return queryset.create(
            FK_User=user,
            MobileNumber=mobile_number,
            IPAddress=user_ip,
            ReferenceCode=reference_code
        )


# Profile (??????????????) Model
class Profile(models.Model):
    SEX_STATUS = (
        ('0', '???????????? ??????????'),
        ('1', '????'),
        ('2', '??????'),
        ('3', '????????'),
    )
    TUTORIALWEB_TYPE = (
        ('0', '?????????? ?????? ??????????'),
        ('1', '???????? ??????????'),
        ('2', '???????? ?????? ??????????????'),
        ('3', '??????????????'),
        ('4', '?????????? ????'),
        ('5', '??????????????'),
        ('6', 'NOD'),
        ('7', '????????'),
        ('8', '?????? ????????'),
    )
    objects = ProfileManager()
    ID = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True)
    FK_User = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        verbose_name='??????????',
        related_name='User_Profile',
        null=True)
    Sex = models.CharField(
        verbose_name='??????????',
        max_length=1,
        choices=SEX_STATUS,
        default='0')
    CountrPreCode = models.CharField(
        verbose_name='???? ????????',
        max_length=6,
        default='098')
    MobileNumber = models.CharField(
        verbose_name='?????????? ????????????',
        max_length=11,
        unique=True)
    ZipCode = models.CharField(
        verbose_name='???? ????????',
        max_length=10,
        blank=True)
    NationalCode = models.CharField(
        verbose_name='???? ??????',
        max_length=10,
        unique=True,
        blank=True,
        null=True)
    Address = models.TextField(verbose_name='????????', blank=True)
    State = models.CharField(verbose_name='??????????', max_length=50, blank=True)
    BigCity = models.CharField(
        verbose_name='??????????????',
        max_length=50,
        blank=True)
    City = models.CharField(verbose_name='??????', max_length=50, blank=True)
    Location = models.CharField(
        verbose_name='???????????? ??????????',
        max_length=150,
        blank=True,
        help_text='?????? ?? ?????? ??????????????????')
    BrithDay = jmodels.jDateField(verbose_name='?????????? ????????', null=True)
    FaxNumber = models.CharField(
        verbose_name='?????????? ??????',
        max_length=8,
        blank=True)
    CityPerCode = models.CharField(
        verbose_name='?????? ??????????',
        max_length=6,
        blank=True,
        default='034')
    PhoneNumber = models.CharField(
        verbose_name='?????????? ???????? ????????',
        max_length=8,
        blank=True)
    Bio = models.CharField(verbose_name='???????????? ????', max_length=250, blank=True)
    Image = models.ImageField(
        verbose_name='??????????????',
        upload_to=PathAndRename('media/Pictures/Profile/'),
        null=True, default='static/Pictures/DefaultProfile.png')
    Image_thumbnail = ImageSpecField(source='Image',
                                     processors=[ResizeToFill(175, 175)],
                                     format='JPEG',
                                     options={'quality': 60})
    ImageNationalCard = models.ImageField(
        verbose_name="?????? ???????? ??????",
        upload_to=PathAndRename('media/Pictures/NationalCard/'),
        null=True, blank=True)
    ImageNationalCardUnverified = models.ImageField(
        verbose_name="?????? ???????? ?????? ?????????? ????????",
        upload_to=PathAndRename('media/Pictures/NationalCard/'),
        null=True, blank=True)
    UserReferenceCode = models.CharField(
        verbose_name='???? ??????', max_length=6, unique=True,
        default=BuildReferenceCode(6))
    Point = models.PositiveIntegerField(verbose_name='???????????? ??????????', default=0)
    TutorialWebsite = models.CharField(
        verbose_name='???????? ???????????? ???? ????????', max_length=1,
        choices=TUTORIALWEB_TYPE, blank=True, default='8')
    ReferenceCode = models.CharField(
        verbose_name='???? ????????', max_length=6, blank=True)
    IPAddress = models.CharField(
        verbose_name='???????? ???? ????',
        max_length=15,
        blank=True)

    # Output Customization Based On UserName (ID)
    def __str__(self):
        return "{} ({})".format(self.FK_User, self.ID)

    def Image_thumbnail_url(self):
        try:
            i = self.Image_thumbnail.url
            url = self.Image_thumbnail.url
            return attach_domain(url)
        except BaseException:
            url = "https://nakhll.com/media/Pictures/avatar.png"
            return url

    def image_national_card_url(self):
        try:
            i = self.ImageNationalCard.url
            url = self.ImageNationalCard.url
            return attach_domain(url)
        except BaseException:
            url = "https://nakhll.com/static-django/images/image_upload.jpg"
            return url

    # Get User Bank Account Info
    def get_bank_account_name(self):
        raise NotImplementedError()

    def get_credit_card_number(self):
        raise NotImplementedError()

    def get_shaba_number(self):
        raise NotImplementedError()

    def chack_user_bank_account(self):
        if (self.get_bank_account_name() is None) or (
                self.get_credit_card_number() is None) or (self.get_shaba_number() is None):
            return True
        else:
            return False

    def is_user_shoper(self):
        if Shop.objects.filter(FK_ShopManager=self.FK_User).exists():
            return True
        else:
            return False

    def get_user_shops(self):
        return Shop.objects.filter(FK_ShopManager=self.FK_User, Publish=True)

    def get_user_products(self):
        return Product.objects.filter(
            FK_Shop__in=self.get_user_shops(),
            Publish=True)

    def get_state_name(self):
        try:
            return State.objects.get(id=self.State).name
        except BaseException:
            return None

    def get_bigcity_name(self):
        try:
            return BigCity.objects.get(id=self.BigCity).name
        except BaseException:
            return None

    def get_city_name(self):
        try:
            return City.objects.get(id=self.City).name
        except BaseException:
            return None

    @property
    def id(self):
        return self.ID

    @property
    def user(self):
        return self.FK_User

    @property
    def first_name(self):
        return self.user.first_name

    @property
    def last_name(self):
        return self.user.last_name

    @property
    def sex(self):
        return self.Sex

    @property
    def birth_day(self):
        return str(self.BrithDay)

    @property
    def counter_pre_code(self):
        return self.CountrPreCode

    @property
    def mobile_number(self):
        return self.MobileNumber

    @property
    def zip_code(self):
        return self.ZipCode

    @property
    def national_code(self):
        return self.NationalCode

    @property
    def address(self):
        return self.Address

    @property
    def state(self):
        return self.State

    @property
    def big_city(self):
        return self.BigCity

    @property
    def city(self):
        return self.City

    @property
    def location(self):
        return self.Location

    @property
    def fax_number(self):
        return self.FaxNumber

    @property
    def city_per_code(self):
        return self.CityPerCode

    @property
    def phone_number(self):
        return self.PhoneNumber

    @property
    def bio(self):
        return self.Bio

    @property
    def image(self):
        return attach_domain(self.Image.url)

    @property
    def image_national_card(self):
        return attach_domain(
            self.ImageNationalCard.url) if self.ImageNationalCard else None

    @property
    def user_reference_code(self):
        return self.UserReferenceCode

    @property
    def point(self):
        return self.Point

    @property
    def tutorial_website(self):
        return self.TutorialWebsite

    @property
    def reference_code(self):
        return self.ReferenceCode

    @property
    def ip_address(self):
        return self.IPAddress

    @property
    def shops(self):
        return self.FK_User.ShopManager.all()

    @property
    def date_joined(self):
        return datetime2jalali(self.FK_User.date_joined, date_only=True)

    # Ordering With DateCreate
    class Meta:
        ordering = ('ID',)
        verbose_name = "??????????????"
        verbose_name_plural = "?????????????? ???? "


# Slider (??????????????) Model
class Slider(models.Model):
    FK_Creator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        verbose_name='?????? ??????????',
        related_name='Slider_Create',
        null=True)
    Title = models.CharField(
        verbose_name='?????????? ?????? ??????????????',
        max_length=100,
        db_index=True)
    Description = models.TextField(
        verbose_name='???????????? ??????????????',
        max_length=350,
        blank=True)
    ShowInfo = models.BooleanField(
        verbose_name='?????????? ?????????? ?????????????? ??????????????', default=True,
        help_text='?????? ???? ???????????? ?????????? ?? ?????????????? ?????? ?????? ???? ?????????? ???????? ???????? ?????? ?????????? ???? ???????? ????????.')
    URL = models.URLField(
        verbose_name='????????',
        help_text='?????????? ???? ???? ???????? ???????? ???? ???? ?????????? ???? ??????',
        blank=True)
    Image = models.ImageField(
        verbose_name='?????? ??????????????',
        upload_to=PathAndRename('media/Pictures/Sliders/'),
        help_text='?????????????? ???? ?????????? ???????? ????????')
    Location = models.IntegerField(verbose_name='???????? ??????????????')
    DateCreate = models.DateTimeField(
        verbose_name='?????????? ???????????????? ??????????????',
        auto_now_add=True)
    DtatUpdate = models.DateTimeField(
        verbose_name='?????????? ?????????????????? ??????????????', auto_now=True)

    AVAILABLE_STATUS = (
        (True, '????????'),
        (False, '?????? ????????'),
    )
    PUBLISH_STATUS = (
        (True, '?????????? ??????'),
        (False, '???? ???????????? ??????????'),
    )
    Available = models.BooleanField(
        verbose_name='?????????? ???????????????? ???????? ??????????',
        choices=AVAILABLE_STATUS,
        default=True)
    Publish = models.BooleanField(
        verbose_name='?????????? ???????????? ???????? ??????????',
        choices=PUBLISH_STATUS,
        default=False)
    FK_User = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        verbose_name='?????????? ??????????',
        related_name='Slider_Accept',
        blank=True,
        null=True)
    BannerBuilder = models.CharField(
        verbose_name='?????? ?????????? ?????????? ??????',
        max_length=120,
        blank=True)
    BannerURL = models.URLField(verbose_name='???????? ?????????? ?????????? ??????', blank=True)

    @property
    def url(self):
        return self.URL

    @property
    def image(self):
        return self.get_image()

    @property
    def title(self):
        return self.Title

    @property
    def show_info(self):
        return self.ShowInfo

    @property
    def description(self):
        return self.Description

    @property
    def location(self):
        return self.Location

    def get_image(self):
        try:
            return attach_domain(self.Image.url)
        except BaseException:
            return None

    # Output Customization Based On Title
    def __str__(self):
        return "{}".format(self.Title)

    # Ordering With id
    class Meta:
        ordering = ('id',)
        verbose_name = "??????????????"
        verbose_name_plural = "?????????????? ????"


# Alert (?????????? ????) Model
class Alert(models.Model):
    class AlertParts:
        ADD_PROFILE = '0'
        EDIT_PROFILE = '1'
        PAYMENT_ERROR = '35'

    FK_User = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        verbose_name='?????? ??????????',
        related_name='User_Registrar_Alert',
        blank=True,
        null=True)
    PART_TYPE = (
        ('0', '?????????? ??????????????'),
        ('1', '???????????? ??????????????'),
        ('2', '?????????? ????????'),
        ('3', '???????????? ????????'),
        ('4', '?????????? ?????? ????????'),
        ('5', '???????????? ?????? ????????'),
        ('6', '?????????? ??????????'),
        ('7', '???????????? ??????????'),
        ('8', '?????????? ?????? ??????????'),
        ('9', '???????????? ?????? ??????????'),
        ('10', '?????????? ?????????? ????????'),
        ('11', '?????? ?????????? ???????? ???????? ??????????'),
        ('12', '?????? ??????????'),
        ('13', '?????? ??????????'),
        ('14', '?????? ?????????? ????????'),
        ('15', '?????? ?????? ?? ?????????? ????????'),
        ('16', '?????? ???????? ????????'),
        ('17', '?????????? ???????? ?????????? ????????'),
        ('18', '?????? ???????????? ?? ?????????????? ???? ??????????'),
        ('19', '?????? ???????? ????????'),
        ('20', '?????????? ??????????'),
        ('21', '?????????? ??????????'),
        ('22', '?????? ?????? ????????'),
        ('23', '?????? ?????? ??????????'),
        ('24', '?????? ?????????? ??????????'),
        ('25', '?????? ???????? ??????????'),
        ('26', '?????????? ????????'),
        ('27', '?????? ????????'),
        ('28', '?????? ?????????? ??????'),
        ('29', '?????? ?????????? ????????????'),
        ('30', '?????? ?????????? ????????'),
        ('31', '?????????????? ??????????'),
        ('32', '?????? ?????????? ?????????????? ????????'),
        ('33', '?????? ?????????? ??????????????'),
        ('34', '?????????? ??????????????????? ??????????????'),
        ('35', '???????? ????????????'),
    )
    Part = models.CharField(
        verbose_name='??????',
        choices=PART_TYPE,
        max_length=2,
        default='0')
    Slug = models.TextField(verbose_name='?????????? ??????', blank=True, null=True)
    SEEN_STATUS = (
        (True, '???????? ??????'),
        (False, '???????? ????????'),
    )
    Seen = models.BooleanField(
        verbose_name='?????????? ????????????',
        choices=SEEN_STATUS,
        default=False)
    STATUS = (
        (True, '?????? ??????????????'),
        (False, '?????? ?????? ??????????????'),
    )
    alert_description = models.TextField(
        verbose_name='??????????????', blank=True, null=True,
        help_text='?????????????? ???? ???????? ??????????')
    Status = models.BooleanField(
        verbose_name='?????????? ??????????????',
        choices=STATUS,
        null=True)
    DateCreate = models.DateTimeField(
        verbose_name='?????????? ?????? ??????????',
        auto_now_add=True)
    DateUpdate = models.DateTimeField(
        verbose_name='?????????? ?????? ??????????????', auto_now=True)
    Description = models.TextField(
        verbose_name='??????????????', blank=True,
        help_text='???? ???????? ?????? ?????????? ?????????????? ?????????? ???????? ???????? ?????????? ???????? ???? ?????????? ???????? ????????????.')
    FK_Staff = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        verbose_name='?????? ??????????',
        related_name='Alert_User_Published',
        blank=True,
        null=True)

    def __str__(self):
        return "{} - {}".format(self.FK_User, self.FK_Staff)

    def get_part_display(self):
        if self.Part == '31':
            return '?????????????? ??????????'

    class Meta:
        ordering = ('id',)
        verbose_name = "??????????"
        verbose_name_plural = "?????????? ????"


# ----------------------------------------------------------------------------------------------------------------------------------
class AmazingProductManager(models.Manager):
    def get_amazing_products(self):
        queryset = self.get_queryset()
        now = timezone.now()
        return queryset.filter(
            start_date__lte=now,
            end_date__gte=now
        )


class AmazingProduct(models.Model):
    objects = AmazingProductManager()
    product = models.ForeignKey(
        Product,
        verbose_name='?????????? ???????? ??????????',
        on_delete=models.SET_NULL,
        null=True,
        related_name='amazing_product',
    )
    start_date = models.DateTimeField(verbose_name='?????????? ????????')
    end_date = models.DateTimeField(verbose_name='?????????? ??????????')

    @property
    def start_date_field(self):
        return self.start_date

    @property
    def end_date_field(self):
        return self.end_date

    class Meta:
        ordering = ('id',)
        verbose_name = "???????? ??????????"
        verbose_name_plural = "???????? ??????????????"

    def __str__(self):
        return self.product.Title


# ----------------------------------------------------------------------------------------------------------------------------------

# State ??????????
class State(models.Model):
    name = models.CharField(verbose_name='?????? ??????????', max_length=127)
    code = models.IntegerField(verbose_name='???? ??????????')

    class Meta:
        ordering = ('id',)
        verbose_name = "??????????"
        verbose_name_plural = "?????????? ????"

    def get_bigcities_of_state(self):
        return self.big_city.all()

    def get_bigcities_of_state_id_name(self):
        return self.get_bigcities_of_state().values('name', 'id')

    def __str__(self):
        return f'{self.name}'


# ???BigCity ??????????????
class BigCity(models.Model):
    name = models.CharField(verbose_name='?????? ??????????????', max_length=127)
    code = models.IntegerField(verbose_name='???? ??????????????')
    state = models.ForeignKey(
        State,
        related_name='big_city',
        on_delete=models.CASCADE)

    class Meta:
        ordering = ('id',)
        verbose_name = "??????????????"
        verbose_name_plural = "?????????????? ????"

    def get_cities_of_bigcities(self):
        return self.city.all()

    def get_cities_of_bigcities_id_name(self):
        return self.get_cities_of_bigcities().values('id', 'name')

    def __str__(self):
        return f'{self.state} - {self.name}'


# ???City ??????
class City(models.Model):
    name = models.CharField(verbose_name='?????? ??????', max_length=127)
    code = models.IntegerField(verbose_name='???? ??????')
    big_city = models.ForeignKey(
        BigCity,
        related_name='city',
        on_delete=models.CASCADE)

    class Meta:
        ordering = ('id',)
        verbose_name = "??????"
        verbose_name_plural = "?????? ????"

    @property
    def value(self):
        return self.id

    @property
    def label(self):
        return self.name

    def __str__(self):
        return f'{self.name} ({self.big_city.state.name})'


class DashboardBannerManager(models.Manager):
    def get_banners(self, banner_status):
        return self.filter(publish_status=banner_status)


class DashboardBanner(models.Model):
    class Meta:
        verbose_name = '?????? ????????????'
        verbose_name_plural = '???????????? ????????????'

    class PublishStatuses(models.TextChoices):
        PUBLISH = 'pub', '?????????? ??????'
        PREVIEW = 'prv', '???????????????????'

    def __str__(self):
        return self.image.name

    image = models.ImageField(
        verbose_name='?????? ??????',
        upload_to=PathAndRename('media/Pictures/Dashboard/Banner/'))
    url = models.URLField(max_length=100, verbose_name='???????? ??????', null=True)
    staff_user = models.ForeignKey(
        User,
        verbose_name='??????????????',
        on_delete=models.SET_NULL,
        null=True,
        related_name='dashboard_banners')
    created_datetime = models.DateTimeField(
        verbose_name='?????????? ??????', auto_now=False, auto_now_add=True)
    publish_status = models.CharField(
        max_length=3, choices=PublishStatuses.choices,
        default=PublishStatuses.PUBLISH)
    objects = DashboardBannerManager()


class LandingPageSchemaManager(models.Manager):
    def is_mobile(self, request):
        return 'Mobile' in request.META['HTTP_USER_AGENT']

    def get_for_device(self, request):
        return self.get_queryset()

    def get_published_schema(self, request):
        return self.get_for_device(request).filter(
            publish_status=LandingPageSchema.PublishStatuses.PUBLISH,
            shoppageschema=None).order_by('order')


class LandingPageSchema(models.Model):
    class Meta:
        verbose_name = '???????????? ???????? ???????? ??????'
        verbose_name_plural = '???????????? ???????? ???????? ??????'

    class PublishStatuses(models.TextChoices):
        PUBLISH = 'pub', '?????????? ??????'
        PREVIEW = 'prv', '???????????????????'

    class ComponentTypes(models.IntegerChoices):
        SLIDER = 1, '??????????????'
        ONE_BANNER = 2, '1 ??????'
        TWO_BANNER = 3, '2 ??????'
        THREE_BANNER = 4, '3 ??????'
        FOUR_BANNER = 5, '4 ??????'
        PRODUCT_ROW = 6, '???????? ??????????'
        PRODUCT_ROW_AMAZING = 7, '???????? ?????????? ???????? ??????????'
        ICON = 8, '????????'

    def __str__(self):
        return 'type:{}, order:{}, data:{}'.format(
            self.get_component_type_display(),
            self.order, self.data)

    component_type = models.IntegerField(
        verbose_name='?????? ???????????? ????????',
        choices=ComponentTypes.choices,
        default=ComponentTypes.ONE_BANNER)
    data = models.URLField(verbose_name='???????? ????', max_length=255)
    title = models.CharField(
        verbose_name='??????????',
        max_length=127,
        null=True,
        blank=True)
    subtitle = models.CharField(
        verbose_name='?????? ??????????',
        max_length=127,
        null=True,
        blank=True)
    url = models.URLField(
        max_length=255,
        verbose_name='????????',
        null=True,
        blank=True)
    background_color = ColorField(
        verbose_name='?????? ???? ??????????',
        null=True,
        blank=True)
    image = models.ImageField(verbose_name='??????', upload_to=PathAndRename(
        'media/Pictures/LandingPage/Schema/'), null=True, blank=True)
    order = models.IntegerField(verbose_name='??????????', default=0)
    staff_user = models.ForeignKey(
        User,
        verbose_name='??????????????',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='landing_page_schemas')
    created_datetime = models.DateTimeField(
        verbose_name='?????????? ??????', auto_now=False, auto_now_add=True)
    publish_status = models.CharField(
        max_length=3, choices=PublishStatuses.choices,
        default=PublishStatuses.PUBLISH)
    is_mobile = models.BooleanField(
        verbose_name='???????????? ???????????? ????????', default=True)
    objects = LandingPageSchemaManager()


class ShopPageSchemaManager(LandingPageSchemaManager):
    def get_published_schema(self, request, shop_id):
        return self.get_for_device(request).filter(
            shop=shop_id, publish_status=ShopPageSchema.PublishStatuses.PUBLISH).order_by('order')

    def get_unpublished_schema(self, request, shop_id):
        return self.get_for_device(request).filter(
            shop=shop_id, publish_status=ShopPageSchema.PublishStatuses.PREVIEW).order_by('order')


class ShopPageSchema(LandingPageSchema):
    class Meta:
        verbose_name = '???????????? ???????? ???????? ???????? ??????'
        verbose_name_plural = '???????????? ???????? ???????? ???????? ??????'

    shop = models.ForeignKey(
        Shop,
        verbose_name='??????????????',
        on_delete=models.CASCADE,
        related_name='shop_page_schemas')
    objects = ShopPageSchemaManager()


class UserImage(models.Model):
    class Meta:
        verbose_name = '?????????? ???????????????? ?????? ??????????'
        verbose_name_plural = '?????????? ???????????????? ?????? ??????????'

    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='uploaded_images',
        verbose_name='??????????')
    title = models.CharField(max_length=100, verbose_name='??????????', blank=True)
    description = models.TextField(verbose_name='??????????????', blank=True)
    image = models.ImageField(
        verbose_name='?????????? ???????????????? ??????',
        upload_to=PathAndRename('media/Pictures/User/UploadedImages/'))
    image_thumbnail = ImageSpecField(
        source='image', processors=[ResizeToFill(180, 180)],
        format='JPEG', options={'quality': 60})
    publish = models.BooleanField(verbose_name='?????????? ???????', default=True)
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='?????????? ??????????')
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name='?????????? ????????????')

    def __str__(self):
        return f'{self.profile.MobileNumber}: {self.title} ({self.image})'


@receiver(models.signals.post_delete, sender=UserImage)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)


@receiver(models.signals.pre_save, sender=UserImage)
def auto_delete_file_on_change(sender, instance, **kwargs):
    if not instance.pk:
        return False
    try:
        old_image = UserImage.objects.get(pk=instance.pk).image
    except UserImage.DoesNotExist:
        return False
    new_image = instance.image
    if not old_image == new_image:
        if os.path.isfile(old_image.path):
            os.remove(old_image.path)


class LandingPage(models.Model):
    class Meta:
        verbose_name = '???????? ????????'
        verbose_name_plural = '???????? ????????'
        ordering = ('-id',)

    class Statuses(models.IntegerChoices):
        INACTIVE = 0, '??????????????'
        ACTIVE = 1, '????????'

    slug = models.CharField(
        max_length=100,
        verbose_name='?????? ????????',
        unique=True)
    status = models.IntegerField(
        verbose_name='??????????',
        choices=Statuses.choices,
        default=Statuses.ACTIVE)
    staff = models.ForeignKey(
        User,
        verbose_name='??????????????',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='landing_pages')
    page_data = models.TextField(
        verbose_name=_('????????????????? ????????'),
        null=True, blank=True)
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='?????????? ??????????')
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name='?????????? ????????????')

    def __str__(self):
        return self.page_slug


class LandingImage(models.Model):
    class Meta:
        verbose_name = '?????????? ???????? ????????'
        verbose_name_plural = '?????????? ???????? ????????'

    landing_page = models.ForeignKey(
        LandingPage,
        verbose_name='???????? ????????',
        on_delete=models.CASCADE,
        related_name='images')
    image = models.ImageField(
        verbose_name='??????????',
        upload_to=PathAndRename('media/Pictures/Landing/'))
    image_thumbnail = ImageSpecField(
        source='image', processors=[ResizeToFill(180, 180)],
        format='JPEG', options={'quality': 60})
    staff = models.ForeignKey(
        User,
        verbose_name='??????????????',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='landing_images')
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='?????????? ??????????')
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name='?????????? ????????????')

    def __str__(self):
        return f'{self.landing_page.page_slug}: {self.image}'


from shop import models as shop_models
