import logging
from uuid import uuid4
from datetime import datetime, timedelta
from django.db import models
from django.conf import settings
from django.db.models.query_utils import Q
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.models import User
from cart.managers import CartManager
from nakhll.utils import datetime2jalali
from nakhll_market.interface import AlertInterface
from nakhll_market.models import Category, Product, Shop
from payoff.models import Transaction
from payoff.interfaces import PaymentInterface
from payoff.exceptions import (
    NoAddressException, InvoiceExpiredException,
    InvalidInvoiceStatusException, NoItemException,
    OutOfPostRangeProductsException
)
from invoice.interfaces import AccountingInterface
from invoice.managers import AccountingManager, InvoiceItemManager
from logistic.models import Address, ShopLogisticUnit
from sms.services import Kavenegar

logger = logging.getLogger(__name__)

# Create your models here.


class Invoice(models.Model):
    class Statuses(models.TextChoices):
        AWAIT_PAYMENT = 'awaiting_paying', _('در انتظار پرداخت')
        AWAIT_SHOP_APPROVAL = 'wait_store_approv', _('در انتظار تأیید فروشگاه')
        PREPATING_PRODUCT = 'preparing_product', _('در حال آماده سازی')
        AWAIT_CUSTOMER_APPROVAL = 'wait_customer_approv', _(
            'در انتظار تأیید مشتری')
        AWAIT_SHOP_CHECKOUT = 'wait_store_checkout', _(
            'در انتظار تسویه با فروشگاه')
        COMPLETED = 'completed', _('تکمیل شده')
        CANCELED = 'canceled', _('لغو شده')

    class Meta:
        verbose_name = _('فاکتور')
        verbose_name_plural = _('فاکتورها')
        ordering = ('-id',)
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name=_('کاربر'))
    old_id = models.UUIDField(null=True, blank=True)
    FactorNumber = models.CharField(
        _('شماره فاکتور'),
        max_length=50,
        null=True,
        blank=True,
        unique=True)
    status = models.CharField(
        _('وضعیت فاکتور'),
        max_length=20,
        default=Statuses.AWAIT_PAYMENT,
        choices=Statuses.choices)
    address_json = models.JSONField(
        _('آدرس ثبت شده نهایی'),
        null=True,
        blank=True,
        encoder=DjangoJSONEncoder)
    invoice_price_with_discount = models.DecimalField(
        _('مبلغ فاکتور با تخفیف'),
        max_digits=12, decimal_places=0, default=0)
    invoice_price_without_discount = models.DecimalField(
        _('مبلغ فاکتور بدون تخفیف'),
        max_digits=12, decimal_places=0, default=0)
    logistic_price = models.DecimalField(
        _('هزینه حمل و نقل'),
        max_digits=12, decimal_places=0, default=0)
    created_datetime = models.DateTimeField(
        _('تاریخ ایجاد فاکتور'), auto_now_add=True)
    payment_request_datetime = models.DateTimeField(
        _('تاریخ درخواست پرداخت'), null=True, blank=True)
    payment_datetime = models.DateTimeField(
        _('تاریخ پرداخت'), null=True, blank=True)
    payment_unique_id = models.BigIntegerField(
        _('شماره درخواست پرداخت'), null=True, blank=True)
    extra_data = models.JSONField(
        null=True, blank=True, encoder=DjangoJSONEncoder)
    total_weight_gram = models.PositiveIntegerField(
        _('وزن نهایی (گرم)'), null=True, blank=True)
    logistic_unit_details = models.JSONField(
        null=True, blank=True, encoder=DjangoJSONEncoder,
        verbose_name=_('جزئیات واحد حمل و نقل'))
    description = models.TextField(
        verbose_name='توضیحات', null=True, blank=True)
    date_checkout = models.DateTimeField(
        verbose_name='تاریخ تسویه', null=True, blank=True)
    date_canceled = models.DateTimeField(
        verbose_name='تاریخ لغو', null=True, blank=True)
    objects = AccountingManager()

    def __str__(self):
        return f'{self.id} ({self.FactorNumber})'

    @property
    def shops(self):
        shop_ids = self.items.values_list(
            'product__FK_Shop__ID', flat=True).distinct()
        return Shop.objects.filter(ID__in=shop_ids)

    @property
    def products(self):
        product_ids = self.items.values_list(
            'product__ID', flat=True).distinct()
        return Product.objects.filter(ID__in=product_ids)

    @property
    def categories(self):
        category_ids = self.items.values_list(
            'product__category__id', flat=True).distinct()
        return Category.objects.filter(id__in=category_ids)

    @property
    def barcodes(self):
        return self.items.exclude(
            barcode=None).values_list('barcode', flat=True)

    @property
    def logistic_errors(self):
        return ""
        # post_setting, is_created = PostPriceSetting.objects.get_or_create()
        # out_of_range = post_setting.get_out_of_range_products(self)
        # return out_of_range

    @property
    def coupons_total_price(self):
        final_price = 0
        usages = self.coupon_usages.all()
        for usage in usages:
            final_price += usage.price_applied
        return final_price

    @property
    def final_price(self):
        ''' Total amount of cart_price + logistic - coupon '''
        total_price = self.invoice_price_with_discount
        logistic_price = self.logistic_price
        coupon_price = self.coupons_total_price
        return total_price + logistic_price - coupon_price

    @property
    def jpayment_datetime(self):
        return datetime2jalali(self.payment_datetime)

    def send_to_payment(self, bank_port=Transaction.IPGTypes.PEC):
        self.__validate_items()
        self.__validate_address()
        self.__validate_invoice_status()
        self.__validate_invoice_expiring_date()
        self.payment_unique_id = int(datetime.now().timestamp() * 1000000)
        self.payment_request_datetime = timezone.now()
        self.save()
        return PaymentInterface.from_invoice(self, bank_port)

    def __validate_items(self):
        if not self.items.count():
            raise NoItemException()

    def __validate_address(self):
        if not self.address_json:
            raise NoAddressException()

    def __validate_invoice_expiring_date(self):
        expire_datetime = self.created_datetime + \
            timedelta(hours=settings.INVOICE_EXPIRING_HOURS)
        if expire_datetime < timezone.now():
            raise InvoiceExpiredException()

    def __validate_invoice_status(self):
        if self.status != self.Statuses.AWAIT_PAYMENT:
            raise InvalidInvoiceStatusException()

    def complete_payment(self):
        ''' Payment is succeeded '''
        self._reduce_inventory()
        self._send_notifications()
        self.status = self.Statuses.AWAIT_SHOP_APPROVAL
        self.payment_datetime = timezone.now()
        self.save()

    def _reduce_inventory(self):
        ''' Reduce bought items from shops stock '''
        items = self.items.all()
        for item in items:
            item.product.reduce_stock(item.count)

    def _send_notifications(self):
        ''' Send SMS to user and shop_owner and create alert for staff'''
        shop_owner_mobiles = self.items.all().values_list(
            'product__FK_Shop__FK_ShopManager__User_Profile__MobileNumber',
            flat=True).distinct()
        logger.debug(f'Shop owner mobiles: {shop_owner_mobiles}')
        for mobile_number in shop_owner_mobiles:
            Kavenegar.shop_new_order(mobile_number, self.id)
        AlertInterface.new_order(self)

    def revert_payment(self):
        ''' Payment is failed'''
        self.unset_coupons()
        self.fill_cart()
        self.status = self.Statuses.AWAIT_PAYMENT
        self.save()

    def unset_coupons(self):
        ''' Delete all coupon usages from invoice '''
        coupon_usages = self.coupon_usages.all()
        for coupon_usage in coupon_usages:
            coupon_usage.delete()

    def available_logistic_units(self):
        ''' Return available logistic units for this invoice '''
        ShopLogisticUnit.objects.filter(
            # Q(shop__ShopProduct=p),
            ~Q(logistic_unit__logistic_unit_constraints__constraint__products__in=self.products),
            ~Q(logistic_unit__logistic_unit_constraints__constraint__categories__in=self.categories),
            ~Q(logistic_unit__logistic_unit_constraints__constraint__cities=self.address.city),
        ).distinct()

    def fill_cart(self):
        cart = CartManager.user_active_cart(self.user)
        for item in self.items.all():
            cart.add_product(item.product)
        cart.reset_coupons()
        cart.reset_address()


class InvoiceItem(models.Model):
    class Meta:
        verbose_name = _('آیتم فاکتور')
        verbose_name_plural = _('آیتم های فاکتور')

    class ItemStatuses(models.TextChoices):
        AWAIT_PAYMENT = 'awaiting_paying', _('در انتظار پرداخت')
        AWAIT_SHOP_APPROVAL = 'wait_store_approv', _('در انتظار تأیید فروشگاه')
        PREPATING_PRODUCT = 'preparing_product', _('در حال آماده سازی')
        AWAIT_CUSTOMER_APPROVAL = 'wait_customer_approv', _(
            'در انتظار تأیید مشتری')
        AWAIT_SHOP_CHECKOUT = 'wait_store_checkout', _(
            'در انتظار تسویه با فروشگاه')
        COMPLETED = 'completed', _('تکمیل شده')
        CANCELED = 'canceled', _('لغو شده')

    class UserConfirmStatuses(models.TextChoices):
        AWAIT_CONFIRM = 'awaiting_confirm', _('در انتظار تایید')
        CONFIRMED = 'confirmed', _('تایید شده')
        REJECTED = 'rejected', _('رد شده')

    class PostType(models.TextChoices):
        IRPOST = 'irpost', _('شرکت پست')
        INCITY = 'incity', _('درون شهری')

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.PROTECT,
        related_name='items',
        verbose_name=_('فاکتور'))
    product = models.ForeignKey(Product, on_delete=models.PROTECT,
                                related_name='invoice_items')
    count = models.IntegerField(_('تعداد'), default=1)
    status = models.CharField(
        _('وضعیت'),
        max_length=20,
        choices=ItemStatuses.choices,
        default=ItemStatuses.AWAIT_PAYMENT)

    slug = models.CharField(max_length=500, null=True, blank=True)
    name = models.CharField(_('نام محصول'), max_length=500)
    price_with_discount = models.DecimalField(
        _('قیمت با تخفیف'), max_digits=12, decimal_places=0)
    price_without_discount = models.DecimalField(
        _('قیمت بدون تخفیف'), max_digits=12, decimal_places=0)
    weight = models.DecimalField(_('وزن'), max_digits=10, decimal_places=0)
    image = models.ImageField(
        _('تصویر'),
        upload_to='invoice_items',
        null=True,
        blank=True,
        max_length=500)
    image_thumbnail = models.ImageField(
        _('تصویر کوچک'),
        upload_to='invoice_items',
        null=True,
        blank=True,
        max_length=500)
    shop_name = models.CharField(_('نام فروشگاه'), max_length=500)
    added_datetime = models.DateTimeField(_('تاریخ افزودن'), auto_now_add=True)
    shop_confirmed_datetime = models.DateTimeField(
        _('تاریخ تایید فروشگاه'), null=True, blank=True)
    post_type = models.CharField(
        _('نوع پست'),
        max_length=20,
        choices=PostType.choices,
        null=True,
        blank=True)
    post_tracking_code = models.CharField(
        _('کد رهگیری پستی'),
        max_length=100, null=True, blank=True)
    user_confirm_datetime = models.DateTimeField(
        _('تاریخ تایید کاربر'), null=True, blank=True)
    user_confirm_status = models.CharField(
        _('وضعیت تایید کاربر'),
        max_length=20,
        choices=UserConfirmStatuses.choices,
        null=True,
        blank=True)
    user_confirm_comment = models.TextField(
        _('توضیحات تایید کاربر'), null=True, blank=True)
    barcode = models.CharField(
        _('کد بارکد'),
        max_length=100,
        null=True,
        blank=True)

    objects = InvoiceItemManager()
