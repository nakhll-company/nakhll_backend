from django.db import models
from django.db.models.aggregates import Sum
from django.db.models.lookups import EndsWith
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.db.models.functions import Cast
from django.core.serializers.json import DjangoJSONEncoder
from rest_framework.exceptions import ValidationError
from coupon.serializers import CouponSerializer
from invoice.models import Invoice, InvoiceItem
from cart.managers import CartItemManager, CartManager
from cart.utils import get_user_or_guest
from logistic.interfaces import LogisticUnitInterface
from logistic.models import Address
from nakhll_market.models import Shop, Product, ProductManager
from nakhll_market.serializers import ProductLastStateSerializer
from payoff.exceptions import NoItemException


class Cart(models.Model):
    class Meta:
        verbose_name = _('سبد خرید')
        verbose_name_plural = _('سبدهای خرید')

    old_id = models.UUIDField(null=True, blank=True)
    user = models.OneToOneField(User, verbose_name=_('کاربر'), on_delete=models.CASCADE,
                                related_name='cart', null=True)
    guest_unique_id = models.CharField(_('شناسه کاربر مهمان'), max_length=100, null=True, blank=True)
    extra_data = models.JSONField(null=True, encoder=DjangoJSONEncoder)
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True,
                                blank=True, related_name='invoices', verbose_name=_('آدرس'))
    logistic_details = models.JSONField(null=True, blank=True, encoder=DjangoJSONEncoder,
                                        verbose_name=_('جزئیات واحد ارسال'))
    coupons = models.ManyToManyField('coupon.Coupon', verbose_name=_('کوپن ها'), blank=True)
    objects = CartManager()

    @property
    def total_discount(self):
        discounts = []
        for item in self.items.all():
            price = item.product.Price 
            old_price = item.product.OldPrice or price
            discount = (old_price - price) * item.count
            discounts.append(discount)
        return sum(discounts)

    @property
    def cart_price(self):
        prices = []
        for item in self.items.all():
            price = item.product.Price 
            prices.append(price * item.count)
        return sum(prices)

    @property
    def cart_old_price(self):
        old_prices= []
        for item in self.items.all():
            price = item.product.Price 
            old_price = item.product.OldPrice or price
            old_prices.append(old_price * item.count)
        return sum(old_prices)

    @property
    def shops(self):
        shop_ids = self.items.values_list('product__FK_Shop__ID', flat=True).distinct()
        return Shop.objects.filter(ID__in=shop_ids)

    @property
    def products(self):
        product_ids = self.items.values_list('product__ID', flat=True).distinct()
        return Product.objects.filter(ID__in=product_ids)

    @property
    def logistic_price(self):
        return self.logistic_details.get('total_price', 0) if self.logistic_details else 0

    @property
    def cart_weight(self):
        return self.items.aggregate(tw=Sum(Cast(
            'product__Weight_With_Packing', output_field=models.IntegerField()
            )))['tw'] or 0

    @property
    def total_price(self):
        total_coupon_price = sum([coupon['price'] for coupon in self.get_coupons_price()])
        return self.cart_price + self.logistic_price - total_coupon_price

    @property
    def ordered_items(self):
        """ Return all cart items in order by shop"""
        return self.items.order_by('-product__FK_Shop')

    def convert_to_invoice(self):
        """ Convert cart to invoice """
        logistic_details = self._generate_logistic_details()
        self._validate_coupons()
        self._validate_items()
        invoice = self._create_invoice(logistic_details)
        self._clear_cart_items()
        return invoice

    def _create_invoice(self, lud):
        invoice = Invoice.objects.create(
            user=self.user,
            created_datetime=timezone.now(),
            invoice_price_with_discount=self.cart_price,
            invoice_price_without_discount=self.cart_old_price,
            total_weight_gram=self.cart_weight,
            logistic_price=lud.total_price,
            logistic_unit_details=lud.as_dict(),
            address_json=self.address.as_json(),
        )

        for coupon in self.coupons.all():
            coupon.apply(invoice)

        cart_items = self.items.all()
        for item in cart_items:
            item.convert_to_invoice_item(invoice)
        
        return invoice

    def _clear_cart_items(self):
        self.items.all().delete()

    def _validate_items(self):
        if self.items.count() < 1:
            raise NoItemException

    def add_product(self, product):
        cart_item = CartItem.objects.filter(product=product, cart=self).first()
        count = cart_item.count + 1 if cart_item else 1

        if not product.is_available():
            raise ValidationError(_('محصول در دسترس نیست'))

        if not ProductManager.has_enough_items_in_stock(product, count):
            raise ValidationError(_('فروشنده قادر به تامین کالا به میزان درخواستی شما نمی‌باشد'))

        product_jsonify = ProductLastStateSerializer(product).data
        if cart_item:
            cart_item.count = count
            cart_item.product_last_state = product_jsonify
            cart_item.save()
        else:
            cart_item = CartItem.objects.create(
                cart=self,
                product=product,
                count=count,
                added_datetime=timezone.now(),
                product_last_state=product_jsonify
            )
        return cart_item

    @staticmethod
    def get_user_cart(request):
        user, guid = get_user_or_guest(request)
        active_cart = CartManager.user_active_cart(user, guid)
        return active_cart

    def get_coupon_errors(self):
        errors = []
        for coupon in self.coupons.all():
            if coupon.is_valid(self):
                continue
            errors.extend(coupon.errors)
        return errors
        
    def get_coupons_price(self):
        result = []
        for coupon in self.coupons.all():
            price = coupon.calculate_coupon_price()
            result.append({
                'coupon': CouponSerializer(coupon).data,
                'price': price
            })
        return result

    def _generate_logistic_details(self):
        lui = LogisticUnitInterface(self)
        lui.generate_logistic_unit_list()
        return lui

    def _validate_coupons(self):
        errors = self.get_coupon_errors()
        if errors:
            raise errors    
        

class CartItem(models.Model):
    class Meta:
        verbose_name = 'کالای سبد خرید'
        verbose_name_plural = 'کالاهای سبد خرید'
    class Statuses(models.TextChoices):


    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, verbose_name=_(
        'آیتم‌های سبد خرید'), related_name='items')
    product = models.ForeignKey(Product, verbose_name=_(
        'محصول'), on_delete=models.CASCADE, related_name='cart_items')
    count = models.PositiveSmallIntegerField(verbose_name=_('تعداد'))
    added_datetime = models.DateTimeField(_('زمان اضافه شدن'), auto_now_add=True)
    product_last_state = models.JSONField(null=True, encoder=DjangoJSONEncoder)
    status = models.CharField(_('Status'), max_length=10, choices=)
    objects = CartItemManager()
    extra_data = models.JSONField(null=True, encoder=DjangoJSONEncoder)

    @property
    def get_total_old_price(self):
        return int(self.product.OldPrice) * self.count

    @property
    def get_total_price(self):
        return int(self.product.Price) * self.count

    def get_cartitem_changes(self):
        """ Check for any changes, show them to user and save new product state as last_known_state """

    def convert_to_invoice_item(self, invoice):
        """ Convert cart item to invoice item """
        # image = self.product.Image if os.path.exists(self.product.Image.path) else None
        # image_thumbnail = self.product.Image_thumbnail if os.path.exists(self.product.Image_thumbnail.path) else None
        InvoiceItem.objects.create(
            invoice=invoice,
            product=self.product,
            count=self.count,
            name=self.product.Title,
            slug=self.product.Slug,
            price_with_discount=self.product.Price,
            price_without_discount=self.product.OldPrice or self.product.Price,
            weight=self.product.Weight_With_Packing,
            # image=image,
            # image_thumbnail=image_thumbnail,
            shop_name=self.product.FK_Shop.Title,
            added_datetime=timezone.now(),
        )

    def reduce_count(self):
        if self.count == 1:
            self.delete()
        else:
            self.count =self.count - 1
            self.save()

