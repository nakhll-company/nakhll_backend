# from datetime import datetime
# from io import BytesIO
# import json
# from django.db.models.expressions import F, Case, ExpressionWrapper, Value, When
# from django.contrib.postgres.aggregates.general import StringAgg
# from django.db.models.fields import CharField, FloatField
# from django.db.models.functions.comparison import Cast
# from django.http import HttpResponse
# from xlsxwriter.workbook import Workbook
# from django.views import View
# from braces.views import GroupRequiredMixin
# from excel_response import ExcelResponse
# from django.db.models import Count, Sum, Q
# from django.db.models.functions import Coalesce
# from django.db.models.functions import Cast
# from django.db.models import DateField

# from nakhll_market.interface import DiscordAlertInterface
# from nakhll_market.models import Profile, Shop, Product
# from logistic.models import ShopLogisticUnit
# from invoice.models import Invoice, InvoiceItem


# class ShopManagersInformation(GroupRequiredMixin, View):
#     """Shop Managers Information"""
#     group_required = u"accounting"

#     def get(self, request):
#         """pylint: disable=unused-argument, missing-docstring"""
#         filename = 'shop_managers_info.xlsx'
#         shops = Shop.objects.all()
#         with BytesIO() as output:
#             workbook = Workbook(output, {'in_memory': True})
#             worksheet = workbook.add_worksheet(filename)
#             # set factor filed
#             worksheet.write_row(0, 0,
#                                 ['نام حجره دار',
#                                  'نام خانوادگی حجره دار',
#                                  'کدملی حجره دار',
#                                  'استان حجره دار',
#                                  'شهرستان حجره دار',
#                                  'شهر حجره دار',
#                                  'نشانی حجره دار',
#                                  'استان حجره',
#                                  'شهرستان حجره',
#                                  'شهر حجره',
#                                  'نشانی حجره',
#                                  ]
#                                 )
#             for row, shop in enumerate(shops):
#                 user = shop.FK_ShopManager
#                 if user:
#                     first_name = user.first_name
#                     last_name = user.last_name
#                 else:
#                     first_name = None
#                     last_name = None
#                 try:
#                     profile = Profile.objects.get(FK_User=user)
#                     national_code = profile.NationalCode
#                     profile_state = profile.State
#                     profile_big_city = profile.BigCity
#                     profile_city = profile.City
#                     profile_location = profile.Location
#                 except BaseException:
#                     national_code = None
#                     profile_state = None
#                     profile_big_city = None
#                     profile_city = None
#                     profile_location = None

#                 worksheet.write_row(row + 1, 0,
#                                     [
#                                         first_name,
#                                         last_name,
#                                         national_code,
#                                         profile_state,
#                                         profile_big_city,
#                                         profile_city,
#                                         profile_location,
#                                         shop.State,
#                                         shop.BigCity,
#                                         shop.City,
#                                         shop.Location,
#                                     ])

#             workbook.close()

#             output.seek(0)

#             response = HttpResponse(
#                 output.read(),
#                 content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
#             response['Content-Disposition'] = "attachment; filename = " + filename

#             output.close()

#         return response


# class ShopManagersInformationV2(GroupRequiredMixin, View):
#     group_required = u"accounting"

#     def get(self, request, *args, **kwargs):
#         filename = 'shop_managers_info'
#         field_header_map = {
#             'FK_ShopManager__first_name': 'نام',
#             'FK_ShopManager__last_name': 'نام خانوادگی',
#             'FK_ShopManager__User_Profile__NationalCode': 'کد ملی',
#             'State': 'استان',
#             'BigCity': 'شهرستان',
#             'City': 'شهر',
#             'Location': 'نشانی',
#         }
#         queryset = Shop.objects.shop_managers_info()
#         return ExcelResponse(
#             data=queryset,
#             output_filename=filename,
#         )


# class UserMobile(View):
#     # group_required = u"marketing"

#     def get(self, request, *args, **kwargs):
#         queryset = Shop.objects.shop_managers_info_marketing()
#         return ExcelResponse(
#             data=queryset,
#         )


# class ProductStats(GroupRequiredMixin, View):
#     group_required = u"factor-stats"

#     def get(self, request):
#         queryset = Product.objects\
#             .annotate(sell_count = Count('invoice_items'),
#             sell_product_count=Sum('invoice_items__count'))\
#             .values(
#                 'Title', 'Slug', 'category__name', 'FK_Shop__Title',
#                 'FK_Shop__Slug', 'FK_Shop__State', 'FK_Shop__BigCity', 'FK_Shop__City',
#                 'FK_Shop__Location', 'FK_Shop__Available', 'FK_Shop__Publish', 
#                 'FK_Shop__FK_ShopManager__username', 'sell_count',
#                 'sell_product_count', 'Price', 'OldPrice', 'DateCreate', 'DateUpdate',
#                 'Inventory', 'Net_Weight', 'Weight_With_Packing',
#                 )
        
#         return ExcelResponse(
#             data=queryset
#         )


# class UserStats(View):
#     def get (self , request):
#         queryset = Profile.objects.select_related('FK_User')\
#             .annotate(shop_count=Count('FK_User__ShopManager')).values(
#             'MobileNumber', 'NationalCode', 'FK_User__first_name',
#             'FK_User__last_name', 'shop_count', 'date_joined')


#         return ExcelResponse(
#             data=queryset
#         )


# class ShopInformation(View):
#     """Shop Information as excel file"""
#     def get(self, request):
#         """pylint: disable=unused-argument, missing-docstring"""
#         queryset = Shop.objects.all()
#         payment_price_filter = Q(
#             ShopProduct__invoice_items__invoice__status__in=[
#                 'preparing_product', 'wait_customer_approv',
#                 'wait_store_checkout', 'completed']
#         )
#         try:
#             start_date_text = request.GET.get('invoice_payment_from', '')
#             start_date = datetime.strptime(start_date_text, '%Y/%m/%d')
#             payment_price_filter &= Q(
#                 ShopProduct__invoice_items__invoice__payment_datetime__gte=start_date)
#         except ValueError:
#             pass
#         queryset = queryset.annotate(
#             available_product=Case(
#                 When(ShopProduct__Available=True, then=Value(1))),
#             available_product_count=Count('available_product'),
#             unavailable_product=Case(
#                 When(ShopProduct__Available=False, then=Value(2))),
#             unavailable_product_count=Count('unavailable_product'),
#             publish_product=Case(
#                 When(ShopProduct__Publish=True, then=Value(3))),
#             publish_product_count=Count('publish_product'),
#             unpublish_product=Case(
#                 When(ShopProduct__Publish=False, then=Value(4))),
#             unpublish_product_count=Count('unpublish_product'),
#             exist_product=Case(
#                 When(ShopProduct__Status='1', then=Value(5))),
#             exist_product_count=Count('exist_product'),
#             production_after_order=Case(
#                 When(ShopProduct__Status='2', then=Value(6))),
#             production_after_order_count=Count('production_after_order'),
#             sale_customization_product=Case(
#                 When(ShopProduct__Status='3', then=Value(7))),
#             sale_customization_product_count=Count('sale_customization_product'),
#             not_exist_product=Case(
#                 When(ShopProduct__Status='4', then=Value(8))),
#             not_exist_product_count=Count('not_exist_product'),
#             invoice_count=Count(
#                 'ShopProduct__invoice_items__invoice',
#                 filter=payment_price_filter),
#             sale_price_sum=Sum(
#                 'ShopProduct__invoice_items__price_with_discount',
#                 filter=payment_price_filter),).values(
#             'Title', 'DateCreate', 'FK_ShopManager__first_name',
#             'FK_ShopManager__last_name','Slug' ,'State', 'BigCity', 'City',
#             'available_product_count', 'unavailable_product_count',
#             'publish_product_count', 'unpublish_product_count',
#             'exist_product_count', 'production_after_order_count',
#             'sale_customization_product_count', 'not_exist_product_count',
#             'FK_ShopManager__User_Profile__MobileNumber', 'invoice_count',
#             'Available', 'Publish', 'FK_ShopManager__last_login',
#             'sale_price_sum')

#         return ExcelResponse(
#             data=queryset
#         )


# class BuyersInfo(GroupRequiredMixin, View):
#     group_required = u"factor-stats"

#     def get(self, request):
#         queryset = InvoiceItem.objects.exclude(status='awaiting_paying').annotate(
#             coupons_total_price=Coalesce(Sum('invoice__coupon_usages__price_applied', output_field=FloatField()), 0),
#             ردیف=Value(' ', output_field=CharField()),
#             شماره_فاکتور=F('invoice__id'),
#             تاریخ_خرید=Cast(F('invoice__payment_datetime'), output_field=DateField()),
#             نام_کالا=StringAgg('product__Title', delimiter=', '),
#             تعداد_کالا=StringAgg(Cast('count', output_field=CharField()), delimiter=', '),
#             مبلغ_هرکالا_باتخفیف=StringAgg(Cast('price_with_discount', output_field=CharField()), delimiter=', '),
#             نام_حجره=StringAgg('product__FK_Shop__Title', delimiter=', ', distinct=True),
#             کدملی_حجره_دار=StringAgg('product__FK_Shop__FK_ShopManager__User_Profile__NationalCode', delimiter=', ', distinct=True),
#             مبلغ_تراکنش=ExpressionWrapper(F('invoice__invoice_price_with_discount') + F('invoice__logistic_price') 
#                         - F('coupons_total_price'), output_field=FloatField()),
#             مبلغ_فاکتور=F('invoice__invoice_price_with_discount'),
#             مبلغ_حمل=F('invoice__logistic_price'),
#             مجموع_کوپن_ها=F('coupons_total_price'),
#             وضعیت_فاکتور=F('invoice__status'),
#             شماره_شبا=StringAgg('product__FK_Shop__bank_account__iban', delimiter=', '),
#             کارمزدنخل=Value(0, output_field=CharField()),
#             مبلغ_پرداختی_کالا=Value(0, output_field=CharField()),
#             طلب_حجره_دار=Value(' ', output_field=CharField()),
#             تاریخ_پرداخت=Value(' ', output_field=CharField()),
#             شماره_شبا_خریدار_جهت_لغو=Value(' ', output_field=CharField()),
#             address_json=F('invoice__address_json'),
#         ).order_by('-invoice__created_datetime')

#         queryset = queryset.values(
#             'ردیف', 'شماره_فاکتور', 'address_json', 'تاریخ_خرید', 'نام_کالا', 'تعداد_کالا', 'نام_حجره', 'مبلغ_هرکالا_باتخفیف',
#             'مبلغ_تراکنش', 'مبلغ_فاکتور', 'مبلغ_حمل', 'مجموع_کوپن_ها', 'وضعیت_فاکتور', 'نام_حجره', 'کدملی_حجره_دار',
#             'شماره_شبا', 'کارمزدنخل', 'کارمزدنخل', 'مبلغ_پرداختی_کالا', 'طلب_حجره_دار', 'تاریخ_پرداخت', 'شماره_شبا_خریدار_جهت_لغو'
#         )
        
#         for q in queryset:
#             address = json.loads(q['address_json']) if q['address_json'] else None
#             q['خریدار'] = address['receiver_full_name'] if address else ''
#             q['شهر_خریدار'] = address['big_city'] if address else ''
#             q['آدرس_خریدار'] = address['address'] if address else ''
#             del q['address_json']

#         return ExcelResponse(data=queryset)


# class InvoicesInfo(GroupRequiredMixin, View):
#     group_required = u"factor-stats"

#     def get(self, request):
#         queryset = Invoice.objects.exclude(status='awaiting_paying').annotate(
#             coupons_total_price=Coalesce(Sum('coupon_usages__price_applied', output_field=FloatField()), 0),
#             ردیف=Value(' ', output_field=CharField()),
#             شماره_فاکتور=F('id'),
#             تاریخ_خرید=Cast(F('payment_datetime'), output_field=DateField()),
#             مبلغ_تراکنش=ExpressionWrapper(F('invoice_price_with_discount') + F('logistic_price') 
#                         - F('coupons_total_price'), output_field=FloatField()),
#             مبلغ_فاکتور=F('invoice_price_with_discount'),
#             مبلغ_حمل=F('logistic_price'),
#             نوع_فاکتور=F('status'),
#             شماره_شبا=StringAgg('items__product__FK_Shop__bank_account__iban', delimiter=', '),
#             کارمزدنخل=Value(0, output_field=CharField()),
#             مبلغ_پرداختی_کالا=Value(0, output_field=CharField()),
#             طلب_حجره_دار=Value(' ', output_field=CharField()),
#             تاریخ_پرداخت=Value(' ', output_field=CharField()),
#         ).order_by('-created_datetime')

#         queryset = queryset.values(
#             'ردیف', 'شماره_فاکتور', 'address_json', 'تاریخ_خرید', 'مبلغ_تراکنش', 'مبلغ_فاکتور', 'مبلغ_حمل', 'نوع_فاکتور', 'شماره_شبا',
#              'کارمزدنخل', 'مبلغ_پرداختی_کالا', 'طلب_حجره_دار', 'تاریخ_پرداخت', 
#         )
        
#         for q in queryset:
#             address = json.loads(q['address_json']) if q['address_json'] else None
#             q['خریدار'] = address['receiver_full_name'] if address else ''
#             q['شهر_خریدار'] = address['big_city'] if address else ''
#             q['آدرس_خریدار'] = address['address'] if address else ''
#             q['بارکدپستی'] = address['zip_code'] if address else ''
#             q['خریدار'] = address['receiver_full_name'] if address else ''
#             del q['address_json']

#         return ExcelResponse(data=queryset)


# class InvoiceStats(GroupRequiredMixin, View):
#     group_required = u"factor-stats"

#     def get(self, request):
#         DiscordAlertInterface.send_alert(
#             'TEST IN INVOICE STATS: Someone get Invoice Stats')
#         queryset = Invoice.objects.filter(
#             FactorNumber=None).annotate(
#             products_list=StringAgg(
#                 'items__product__Title',
#                 delimiter=', '),
#             shops_list=StringAgg(
#                 'items__product__FK_Shop__Title',
#                 delimiter=', ',
#                 distinct=True),
#             coupons_list=StringAgg(
#                 'coupon_usages__coupon__code',
#                 delimiter=', '),
#             coupons_total_price=Coalesce(
#                 Sum(
#                     'coupon_usages__price_applied',
#                     output_field=FloatField()),
#                 0.0),
#             total_price=ExpressionWrapper(
#                 F('invoice_price_with_discount') +
#                 F('logistic_price') -
#                 F('coupons_total_price'),
#                 output_field=FloatField())).order_by('-created_datetime')

#         queryset = queryset.values(
#             'id',
#             'user__username',
#             'user__User_Profile__MobileNumber',
#             'address_json',
#             'coupons_list',
#             'products_list',
#             'shops_list',
#             'invoice_price_with_discount',
#             'invoice_price_without_discount',
#             'logistic_price',
#             'coupons_total_price',
#             'status',
#             'created_datetime',
#             'payment_datetime',
#             'total_weight_gram',
#             'total_price',
#         )

#         for q in queryset:
#             address = json.loads(
#                 q['address_json']) if q['address_json'] else None
#             q['city'] = address['city'] if address else ''
#             q['big_city'] = address['big_city'] if address else ''
#             q['state'] = address['state'] if address else ''
#             q['address'] = address['address'] if address else ''
#             q['zip_code'] = address['zip_code'] if address else ''
#             q['phone_number'] = address['phone_number'] if address else ''
#             q['receiver_full_name'] = address['receiver_full_name'] if address else ''
#             q['receiver_mobile_number'] = address['receiver_mobile_number'] if address else ''
#             del q['address_json']

#         return ExcelResponse(data=queryset)


# class ShopLogisticUnitView(View):

#     def get(self, request):
#         DiscordAlertInterface.send_alert(
#             'TEST IN SHOP LOGISTIC UNIT STATS: Someone get Shop Logistic Unit Stats')
#         queryset = ShopLogisticUnit.objects.values(
#             'shop__Title', 'name', 'logo', 'logo_type', 'is_active', 'is_publish', 'description','created_at',
#             'updated_at', 'constraint__categories', 'constraint__cities', 'constraint__max_weight',
#             'constraint__min_weight', 'constraint__max_cart_price', 'constraint__min_cart_price',
#             'constraint__max_cart_count', 'constraint__min_cart_count', 'calculation_metric__price_per_kilogram',
#             'calculation_metric__price_per_extra_kilogram', 'calculation_metric__pay_time', 'calculation_metric__payer'
#             )
#         return ExcelResponse(data = queryset)
