from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.safestring import mark_safe
import jdatetime
import json
from django.contrib import admin
from django.utils.timezone import localtime
from django.utils import timezone
from invoice.models import Invoice, InvoiceItem
from coupon.models import CouponUsage

# Register your models here.


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    fields = (
        'product_name',
        'count',
        'price_with_discount',
        'price_without_discount',
        'weight',
        'shop_name',
        'preparation',
        'barcode')
    readonly_fields = fields
    extra = 0

    def product_name(self, obj):
        return mark_safe(
            '<a href="{}">{}</a>'.format(
                reverse(
                    "admin:nakhll_market_product_change",
                    args=(obj.product.pk,)),
                obj.product))
    product_name.short_description = 'نام محصول'

    def preparation(self, obj):
        return obj.product.PreparationDays
    preparation.short_description = 'زمان آماده سازی'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product')

class CouponUsageInline(admin.TabularInline):
    model = CouponUsage
    extra = 0
    fields = ('coupon', 'price_applied', )
    # readonly_fields = ('coupon', 'used_count', 'used_at', )


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'status',
        'is_payed',
        'final_price',
        'post_price',
        'coupons_total_price',
        'receiver_full_name',
        'created_datetime_jalali',
        'post_tracking_code',
    )
    list_filter = ('status',)
    ordering = ['-created_datetime', ]
    search_fields = ('id', 'FactorNumber')
    fields = (
        'id',
        'user',
        'old_id',
        'FactorNumber',
        'status',
        'display_address',
        'invoice_price_with_discount',
        'invoice_price_without_discount',
        'logistic_price',
        'payment_request_datetime',
        'payment_datetime',
        'logistic_unit_details',
        'payment_unique_id',
        'total_weight_gram',
        'final_price',
        'shop_iban',
        'is_payed',
        'created_datetime_jalali',
        'coupons_total_price',
        'description',
        'date_checkout',
        'date_canceled')
    readonly_fields = (
        'id',
        'user',
        'old_id',
        'FactorNumber',
        'status',
        'display_address',
        'invoice_price_with_discount',
        'invoice_price_without_discount',
        'logistic_price',
        'payment_request_datetime',
        'payment_datetime',
        'logistic_unit_details',
        'payment_unique_id',
        'total_weight_gram',
        'final_price',
        'shop_iban',
        'is_payed',
        'created_datetime_jalali',
        'coupons_total_price')

    inlines = [InvoiceItemInline, CouponUsageInline]
    change_form_template = "admin/custom/invoice_changeform.html"

    def receiver_full_name(self, obj):
        if obj.address_json:
            address = json.loads(obj.address_json)
            return address.get('receiver_full_name', '')
        return ''
    receiver_full_name.short_description = 'نام گیرنده'

    def created_datetime_jalali(self, obj):
        localtime_time = localtime(obj.created_datetime)
        return jdatetime.datetime.fromgregorian(
            datetime=localtime_time).strftime('%Y/%m/%d %H:%M:%S')
    created_datetime_jalali.short_description = 'تاریخ ثبت'

    def shop_iban(self, obj):
        text = ''
        for shop in obj.shops.all():
            text += f'{shop.Title}: {shop.bank_account.iban}\n'
        return text
    shop_iban.short_description = 'شماره حساب'

    def is_payed(self, obj: Invoice):
        return not obj.status == obj.Statuses.AWAIT_PAYMENT
    is_payed.short_description = 'پرداخت شده؟'
    is_payed.boolean = True

    def final_price(self, obj):
        return f'{obj.final_price:,} ریال'
    final_price.short_description = 'قیمت نهایی'

    def post_price(self, obj):
        return f'{obj.logistic_price:,} ریال'
    post_price.short_description = 'هزینه ارسال'

    def post_tracking_code(self, obj):
        barcodes_set = set()
        for item in obj.items.all():
            if item.barcode:
                barcodes_set.add(item.barcode)
        return ','.join(barcodes_set)
    post_tracking_code.short_description = 'بارکد رهگیری پستی'

    def coupons_total_price(self, obj):
        return f'{obj.coupons_total_price:,} ریال'
    coupons_total_price.short_description = 'هزینه کوپن'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user').prefetch_related('items').prefetch_related('coupon_usages')

    def display_address(self, obj):
        if obj.address_json:
            address = json.loads(obj.address_json)
            state = address.get('state', '')
            big_city = address.get('big_city', '')
            city = address.get('city', '')
            address_text = address.get('address', '')
            zip_code = address.get('zip_code', '')
            reveiver_name = address.get('receiver_full_name', '')
            reveiver_mobile_number = address.get('receiver_mobile_number', '')
            return (f'{state}, {big_city}, {city}, {address_text}\n'
                    f'کد پستی: {zip_code} - گیرنده:{reveiver_name}'
                    f'- شماره تماس:{reveiver_mobile_number}')
        return '-'
    display_address.short_description = 'آدرس'

    def response_change(self, request, obj: Invoice):
        if "checkout_invoice" in request.POST:
            if request.user.has_perm('invoice.checkout_invoice'):
                obj.status = obj.Statuses.COMPLETED
                obj.date_checkout = timezone.now()
                obj.save()
                self.message_user(request, "فاکتور با موفقیت تسویه شد.")
                return HttpResponseRedirect(".")
            else:
                self.message_user(
                    request, "شما دسترسی لازم برای این کار را ندارید")
                return HttpResponseRedirect(".")
        if "cancel_invoice" in request.POST:
            if request.user.has_perm('invoice.cancel_invoice'):
                obj.status = obj.Statuses.CANCELED
                obj.date_canceled = timezone.now()
                obj.save()
                self.message_user(request, "فاکتور با موفقیت لغو شد.")
                return HttpResponseRedirect(".")
            else:
                self.message_user(
                    request, "شما دسترسی لازم برای این کار را ندارید")
                return HttpResponseRedirect(".")

        return super().response_change(request, obj)
