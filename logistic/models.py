import json
from django.db import models
from django.core.files import File
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from nakhll_market.models import Category, Product, Shop, State, BigCity, City
from logistic.managers import AddressManager, ShopLogisticUnitManager


# Create your models here.

class Address(models.Model):
    ''' Addresses across all project '''
    class Meta:
        verbose_name = _('آدرس')
        verbose_name_plural = _('آدرس‌ها')
    old_id = models.UUIDField(null=True, blank=True)
    user = models.ForeignKey(User, verbose_name=_(
        'کاربر'), related_name='addresses', on_delete=models.CASCADE)
    state = models.ForeignKey(State, verbose_name=_(
        'استان'), related_name='addresses', on_delete=models.CASCADE)
    big_city = models.ForeignKey(BigCity, verbose_name=_(
        'شهرستان'), related_name='addresses', on_delete=models.CASCADE)
    city = models.ForeignKey(City, verbose_name=_(
        'شهر'), related_name='addresses', on_delete=models.CASCADE)
    address = models.TextField(verbose_name=_('آدرس'))
    zip_code = models.CharField(verbose_name=_('کد پستی'), max_length=10)
    phone_number = models.CharField(verbose_name=_(
        'تلفن ثابت'), max_length=11, null=True, blank=True)
    receiver_full_name = models.CharField(verbose_name=_(
        'نام و نام خانوادگی گیرنده'), max_length=200)
    receiver_mobile_number = models.CharField(
        verbose_name=_('تلفن همراه گیرنده'), max_length=11)

    objects = AddressManager()

    def __str__(self):
        return f'{self.user}: {self.address}'

    def as_json(self):
        address_data = {
            'state': self.state.name,
            'big_city': self.big_city.name,
            'city': self.city.name,
            'address': self.address,
            'zip_code': self.zip_code,
            'phone_number': self.phone_number,
            'receiver_full_name': self.receiver_full_name,
            'receiver_mobile_number': self.receiver_mobile_number
        }
        return json.dumps(address_data, ensure_ascii=False)


class ShopLogisticUnit(models.Model):
    class Meta:
        verbose_name = _('واحد ارسال فروشگاه')
        verbose_name_plural = _('واحد ارسال فروشگاه')
        ordering = ['-id']

    class LogoType(models.IntegerChoices):
        CUSTOM = 0, _('لوگوی شخصی')
        PPOST = 1, _('پست پیشتاز')
        SPOST = 2, _('پست سفارشی')
        DELIVERY = 3, _('پیک')
        PAD = 4, _('پسکرایه')
        FREE = 5, _('رایگان')

    shop = models.ForeignKey(
        Shop,
        verbose_name=_('حجره'),
        related_name='logistic_units',
        on_delete=models.CASCADE)
    name = models.CharField(verbose_name=_('نام واحد'), max_length=200)
    logo = models.ImageField(
        verbose_name=_('لوگو'),
        upload_to='media/Pictures/logistic_unit/defaults',
        null=True,
        blank=True,
        default='static/Pictures/unkown_lu.png')
    logo_type = models.IntegerField(
        verbose_name=_('نوع لوگو'),
        choices=LogoType.choices,
        default=LogoType.CUSTOM)
    is_active = models.BooleanField(verbose_name=_('فعال؟'), default=True)
    is_publish = models.BooleanField(verbose_name=_('منتشر شود؟'), default=True)
    description = models.TextField(
        verbose_name=_('توضیحات'),
        null=True, blank=True)
    created_at = models.DateTimeField(
        verbose_name=_('تاریخ ایجاد'),
        auto_now_add=True)
    updated_at = models.DateTimeField(
        verbose_name=_('تاریخ بروزرسانی'), auto_now=True)
    objects = ShopLogisticUnitManager()

    def __str__(self):
        return f'{self.shop}: {self.name}'

    def save(self, **kwargs):
        self.save_logo()
        return super().save(**kwargs)

    def save_logo(self):
        if self.logo_type != self.LogoType.CUSTOM:
            self.logo = File(
                open(
                    f'static/Pictures/{self.logo_type}.png',
                    'rb'))


class ShopLogisticUnitConstraint(models.Model):
    class Meta:
        verbose_name = _('محدودیت واحد ارسال فروشگاه')
        verbose_name_plural = _('محدودیت واحد ارسال فروشگاه')
        ordering = ['-id']

    shop_logistic_unit = models.OneToOneField(
        ShopLogisticUnit, verbose_name=_('واحد ارسال'),
        related_name='constraint', on_delete=models.CASCADE)
    cities = models.ManyToManyField(
        City, verbose_name=_('شهرها'),
        related_name='logistic_unit_constraints', blank=True)
    products = models.ManyToManyField(
        Product, verbose_name=_('محصولات'),
        related_name='logistic_unit_constraints', blank=True)
    categories = models.ManyToManyField(
        Category, verbose_name=_('دسته بندی ها'),
        related_name='logistic_unit_constraints', blank=True)
    max_weight = models.PositiveIntegerField(
        verbose_name=_('حداکثر وزن (کیلوگرم)'),
        default=0, null=True, blank=True)
    min_weight = models.PositiveIntegerField(
        verbose_name=_('حداقل وزن (کیلوگرم)'),
        default=0, null=True, blank=True)
    max_cart_price = models.PositiveIntegerField(
        verbose_name=_('حداکثر قیمت سبد خرید (ریال)'),
        default=0, null=True, blank=True)
    min_cart_price = models.PositiveIntegerField(
        verbose_name=_('حداقل قیمت سبد خرید (ریال)'),
        default=0, null=True, blank=True)
    max_cart_count = models.PositiveIntegerField(
        verbose_name=_('حداکثر تعداد سبد خرید'),
        default=0, null=True, blank=True)
    min_cart_count = models.PositiveIntegerField(
        verbose_name=_('حداقل تعداد سبد خرید'),
        default=0, null=True, blank=True)
    created_at = models.DateTimeField(
        verbose_name=_('تاریخ ایجاد'),
        auto_now_add=True)
    updated_at = models.DateTimeField(
        verbose_name=_('تاریخ بروزرسانی'), auto_now=True)

    def __str__(self):
        return f'{self.shop_logistic_unit} - {self.cities.count()} - {self.products.count()}'


class ShopLogisticUnitCalculationMetric(models.Model):
    class Meta:
        verbose_name = _('پارامتر‌ محاسبه واحد ارسال فروشگاه')
        verbose_name_plural = _('پارامتر‌ محاسبه واحد ارسال فروشگاه')
        ordering = ['-id']

    class PayTimes(models.TextChoices):
        WHEN_BUYING = 'when_buying', _('هنگام خرید')
        AT_DELIVERY = 'at_delivery', _('هنگام تحویل')

    class PayerTypes(models.TextChoices):
        SHOP = 'shop', _('فروشگاه')
        CUSTOMER = 'cust', _('مشتری')

    shop_logistic_unit = models.OneToOneField(
        ShopLogisticUnit, verbose_name=_('واحد ارسال'),
        related_name='calculation_metric', on_delete=models.CASCADE)
    price_per_kilogram = models.FloatField(
        verbose_name=_('قیمت به ازای هر کیلو (ریال)'), default=0)
    price_per_extra_kilogram = models.FloatField(
        verbose_name=_('قیمت به ازای هر کیلو اضافه (ریال)'), default=0)
    pay_time = models.CharField(
        verbose_name=_('زمان پرداخت'),
        max_length=11,
        choices=PayTimes.choices,
        default=PayTimes.WHEN_BUYING)
    payer = models.CharField(
        verbose_name=_('پرداخت کننده'),
        max_length=4,
        choices=PayerTypes.choices,
        default=PayerTypes.CUSTOMER)
    created_at = models.DateTimeField(
        verbose_name=_('تاریخ ایجاد'),
        auto_now_add=True)
    updated_at = models.DateTimeField(
        verbose_name=_('تاریخ بروزرسانی'), auto_now=True)

    def __str__(self):
        return f'{self.shop_logistic_unit} - {self.price_per_kilogram} - {self.price_per_extra_kilogram}'


class LogisticUnitGeneralSetting(models.Model):
    class Meta:
        verbose_name = _('تنظیمات واحد ارسال')
        verbose_name_plural = _('تنظیمات واحد ارسال')

    class Name(models.IntegerChoices):
        '''it's used as logo_type in generate_logistic_units'''
        PPOST = 1, _('پست پیشتاز')
        SPOST = 2, _('پست سفارشی')
        DELIVERY = 3, _('پیک')
        PAD = 4, _('پسکرایه')
        FREE = 5, _('ارسال رایگان')

    name = models.IntegerField(
        verbose_name=_('نوع ارسال پستی'),
        choices=Name.choices,
        unique=True,
        default=Name.PPOST)
    default_price_per_kilogram = models.PositiveIntegerField(
        verbose_name=_('قیمت به ازای هر کیلو (ریال)'), default=0)
    default_price_per_extra_kilogram = models.PositiveIntegerField(
        verbose_name=_('قیمت به ازای هر کیلو اضافه (ریال)'), default=0)
    maximum_price_per_kilogram = models.PositiveIntegerField(
        verbose_name=_('حداکثر قیمت به ازای هر کیلو (ریال)'), default=0)
    maximum_price_per_extra_kilogram = models.PositiveIntegerField(
        verbose_name=_('حداکثر قیمت به ازای هر کیلو اضافه (ریال)'), default=0)
    is_active = models.BooleanField('فعال', default=True)
    is_only_for_shop_city = models.BooleanField(
        'فقط برای شهر حجره فعال می باشد', default=False)
    created_at = models.DateTimeField(
        verbose_name=_('تاریخ ایجاد'),
        auto_now_add=True)
    updated_at = models.DateTimeField(
        verbose_name=_('تاریخ بروزرسانی'), auto_now=True)
    updated_by = models.ForeignKey(
        User, verbose_name=_('بروزرسانی توسط'),
        on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f'{self.default_price_per_kilogram} - {self.default_price_per_extra_kilogram}'

    def clean(self):
        ''' we have only two object on for pishtaz another for sefareshi '''
        super().clean()
        lugs = LogisticUnitGeneralSetting.objects.filter(name=self.name)
        if lugs:
            self.pk = lugs[0].pk


############################ COMPLEX MODELS ###############################

# class LogisticUnitMetric(models.Model):
#     class Meta:
#         verbose_name = _('متریک ارسال')
#         verbose_name_plural = _('متریک ارسال')

#     price_per_kg = models.PositiveIntegerField(
#         verbose_name=_('قیمت هر کیلوگرم'), null=True, blank=True)
#     price_per_extra_kg = models.PositiveIntegerField(
#         verbose_name=_('قیمت هر کیلوگرم اضافه'), null=True, blank=True)
#     is_default = models.BooleanField(default=False, verbose_name=_('پیش فرض؟'))
#     created_by = models.ForeignKey(
#         User, on_delete=models.SET_NULL, null=True, verbose_name=_('ایجاد کننده'))
#     created_at = models.DateTimeField(_('تاریخ ایجاد'), auto_now_add=True)
#     updated_at = models.DateTimeField(_('تاریخ بروزرسانی'), auto_now=True)

#     def __str__(self):
# return f'IsDefault: {self.is_default} (ppkg: {self.price_per_kg}, ppekg:
# {self.price_per_extra_kg})'


# class LogisticUnitConstraintParameter(models.Model):
#     class Meta:
#         verbose_name = _('پارامتر محدودیت ارسال')
#         verbose_name_plural = _('پارامتر محدودیت ارسال')

#     cities = models.ManyToManyField(City, verbose_name=_('شهرها'))
#     products = models.ManyToManyField(Product, verbose_name=_('محصولات'))
#     min_price = models.DecimalField(verbose_name=_(
#         'حداقل قیمت'), max_digits=10, decimal_places=2, null=True, blank=True)
#     categories = models.ManyToManyField(
#         Category, verbose_name=_('دسته بندی ها'))
#     max_weight_g = models.PositiveIntegerField(
#         verbose_name=_('حداکثر وزن (گرم)'), null=True, blank=True)
#     max_package_value = models.PositiveIntegerField(
#         verbose_name=_('حداکثر ارزش بسته'), null=True, blank=True)
#     created_by = models.ForeignKey(
#         User, on_delete=models.SET_NULL, null=True, verbose_name=_('ایجاد کننده'))
#     created_at = models.DateTimeField(_('تاریخ ایجاد'), auto_now_add=True)
#     updated_at = models.DateTimeField(_('تاریخ بروزرسانی'), auto_now=True)

#     def __str__(self):
# return f'MinPrice: {self.min_price} (MaxWeight: {self.max_weight_g},
# MaxPackageValue: {self.max_package_value})'


# class LogisticUnit(models.Model):
#     class Meta:
#         verbose_name = _('واحد ارسال')
#         verbose_name_plural = _('واحد ارسال')

#     name = models.CharField(max_length=50, verbose_name=_('نام  '))
#     description = models.TextField(
#         null=True, blank=True, verbose_name=_('توضیحات'))
#     is_publish = models.BooleanField(
#         default=True, verbose_name=_('منتشر شده؟'))
#     metric = models.ForeignKey(
#         LogisticUnitMetric, on_delete=models.SET_NULL, null=True, verbose_name=_('متریک'))
#     is_always_active = models.BooleanField(default=False, verbose_name=_('همیشه فعال؟'),
#                                            help_text='در صورتی که فعال باشد، امکان غیر فعال سازی توسط کاربر وجود ندارد.')
#     priority = models.PositiveIntegerField(default=0, verbose_name=_('اولویت'))
#     is_default_logistic_unit = models.BooleanField(default=False, verbose_name=_('واحد پیش فرض ارسال؟'),
#                                       help_text=_('در صورت عدم نبود واحد ارسال دیگر، این واحد ارسال پیش فرض خواهد بود.'))
#     created_by = models.ForeignKey(
#         User, on_delete=models.SET_NULL, null=True, verbose_name=_('ایجاد کننده'))
#     created_at = models.DateTimeField(_('تاریخ ایجاد'), auto_now_add=True)
#     updated_at = models.DateTimeField(_('تاریخ بروزرسانی'), auto_now=True)

#     def __str__(self):
#         return self.name

#     @staticmethod
#     def sync_shop(shop):
#         all_logistic_units_ids = LogisticUnit.objects.filter(is_publish=True).values_list('id', flat=True)
#         shop_logistic_units_ids = ShopLogisticUnit.objects.filter(
#                 shop=shop, logistic_unit__is_publish=True
#             ).values_list('logistic_unit_id', flat=True)
#         for id in all_logistic_units_ids:
#             if id not in shop_logistic_units_ids:
#                 ShopLogisticUnit.objects.create(shop=shop, logistic_unit_id=id)


# class LogisticUnitConstraint(models.Model):
#     class Meta:
#         verbose_name = _('محدودیت ارسال')
#         verbose_name_plural = _('محدودیت ارسال')

#     logistic_unit = models.ForeignKey(
#         LogisticUnit, on_delete=models.SET_NULL, null=True, verbose_name=_('واحد ارسال'),
#         related_name='logistic_unit_constraints')
#     constraint = models.ForeignKey(LogisticUnitConstraintParameter,
#                                    on_delete=models.SET_NULL, null=True, verbose_name=_('محدودیت'))
#     is_publish = models.BooleanField(
#         default=True, verbose_name=_('منتشر شده؟'))
#     created_by = models.ForeignKey(
#         User, on_delete=models.SET_NULL, null=True, verbose_name=_('ایجاد کننده'))
#     created_at = models.DateTimeField(_('تاریخ ایجاد'), auto_now_add=True)
#     updated_at = models.DateTimeField(_('تاریخ بروزرسانی'), auto_now=True)

#     def __str__(self):
#         return self.logistic_unit.name + ' - ' + self.constraint.__str__()


# class ShopLogisticUnit(models.Model):
#     class Meta:
#         verbose_name = _('واحد ارسال فروشگاه')
#         verbose_name_plural = _('واحد ارسال فروشگاه')

#     shop = models.ForeignKey(
#         Shop, on_delete=models.SET_NULL, null=True, verbose_name=_('فروشگاه'), related_name='shop_logistic_units')
#     logistic_unit = models.ForeignKey(
#         LogisticUnit, on_delete=models.SET_NULL, null=True, verbose_name=_('واحد ارسال'))
#     is_active = models.BooleanField(default=True, verbose_name=_('فعال؟'))
#     use_default_setting = models.BooleanField(
#         default=True, verbose_name=_('استفاده از تنظیم پیش فرض؟'))
#     created_at = models.DateTimeField(_('تاریخ ایجاد'), auto_now_add=True)
#     updated_at = models.DateTimeField(_('تاریخ بروزرسانی'), auto_now=True)

#     def __str__(self):
#         return self.shop.Slug + ' - ' + self.logistic_unit.name


# class ShopLogisticUnitConstraint(models.Model):
#     class Meta:
#         verbose_name = _('محدودیت ارسال فروشگاه')
#         verbose_name_plural = _('محدودیت ارسال فروشگاه')

#     shop_logistic_unit = models.ForeignKey(
#         ShopLogisticUnit, on_delete=models.SET_NULL, null=True, verbose_name=_('واحد ارسال فروشگاه'), related_name='shop_logistic_unit_constraints')
#     constraint = models.OneToOneField(LogisticUnitConstraintParameter, on_delete=models.SET_NULL, null=True, verbose_name=_(
#         'محدودیت'), related_name='shop_logistic_unit_constraint')
#     is_active = models.BooleanField(default=True, verbose_name=_('فعال؟'))
#     created_at = models.DateTimeField(_('تاریخ ایجاد'), auto_now_add=True)
#     updated_at = models.DateTimeField(_('تاریخ بروزرسانی'), auto_now=True)

#     def __str__(self):
# return self.shop_logistic_unit.__str__() + ' - ' +
# self.constraint.__str__()


# class ShopLogisticUnitMetric(models.Model):
#     class Meta:
#         verbose_name = _('متریک فروشگاه')
#         verbose_name_plural = _('متریک فروشگاه')

#     shop_logistic_unit_constraint = models.OneToOneField(
#                     ShopLogisticUnitConstraint,
#                     on_delete=models.SET_NULL,
#                     null=True, related_name='shop_logistic_unit_metric',
#                     verbose_name=_('واحد ارسال فروشگاه'))
#     metric = models.OneToOneField(
#         LogisticUnitMetric, on_delete=models.SET_NULL, null=True, verbose_name=_('متریک'))
#     created_at = models.DateTimeField(_('تاریخ ایجاد'), auto_now_add=True)
#     updated_at = models.DateTimeField(_('تاریخ بروزرسانی'), auto_now=True)

#     def __str__(self):
# return self.shop_logistic_unit_constraint.__str__() + ' - ' +
# self.metric.__str__()
