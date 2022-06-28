from django.db.models import Q, Count
from import_export import resources
from import_export.fields import Field
from nakhll_market.models import Profile, Shop

class ProfileResource(resources.ModelResource):
    first_name = Field(
        attribute='first_name',
        column_name='نام',
        readonly=True)
    last_name = Field(
        attribute='last_name',
        column_name='نام خانوادگی',
        readonly=True)
    mobile_number = Field(
        attribute='mobile_number',
        column_name='شماره موبایل',
        readonly=True)
    national_code = Field(
        attribute='national_code',
        column_name='کد ملی',
        readonly=True)
    date_joined = Field(
        attribute='date_joined',
        column_name='تاریخ عضویت',
        readonly=True)
    shop_count = Field(
        attribute='shop_count',
        column_name='تعداد حجره',
        readonly=True)

    class Meta:
        model = Profile


class ShopStatisticResource(resources.ModelResource):
    id = Field(
        attribute='id',
        column_name='آی دی',
        readonly=True)
    title = Field(
        attribute='title',
        column_name='عنوان',
        readonly=True)
    slug = Field(
        attribute='slug',
        column_name='شناسه',
        readonly=True)
    products_count = Field(
        attribute='products_count',
        column_name='تعداد محصول',
        readonly=True)
    date_created = Field(
        attribute='date_created',
        column_name='تاریخ ساخت',
        readonly=True)
    total_sell = Field(
        attribute='total_sell',
        column_name='تعداد فروش نوع محصول',
        readonly=True)
    manager_mobile_number = Field(
        attribute='manager_mobile_number',
        column_name='شماره مدیر فروشگاه',
        readonly=True)

    class Meta:
        model = Shop
        fields = ('id', 'title', 'slug', 'products_count',
                  'date_created', 'total_sell', 'manager_mobile_number')

    def get_queryset(self):
        return Shop.objects.select_related('FK_ShopManager').annotate(
            # products_count=Count('ShopProduct'),
            total_sell=Count('ShopProduct__invoice_items',
                             filter=Q(
                                 Q(ShopProduct__invoice_items__invoice__status='wait_store_approv') |
                                 Q(ShopProduct__invoice_items__invoice__status='preparing_product') |
                                 Q(ShopProduct__invoice_items__invoice__status='wait_customer_approv') |
                                 Q(ShopProduct__invoice_items__invoice__status='wait_store_checkout') |
                                 Q(ShopProduct__invoice_items__invoice__status='completed')
                             )
                             )
        )


class ShopAdminResource(resources.ModelResource):
    title = Field(
        attribute='title',
        column_name='عنوان',
        readonly=True)
    slug = Field(
        attribute='slug',
        column_name='شناسه',
        readonly=True)
    date_created = Field(
        attribute='date_created',
        column_name='تاریخ ساخت',
        readonly=True)
    date_updated = Field(
        attribute='date_updated',
        column_name='تاریخ بروزرسانی',
        readonly=True)
    state = Field(
        attribute='state',
        column_name='استان',
        readonly=True)
    city = Field(
        attribute='city',
        column_name='شهر',
        readonly=True)
    products_count = Field(
        attribute='products_count',
        column_name='تعداد محصول',
        readonly=True)
    total_sell = Field(
        attribute='total_sell',
        column_name='فروش حجره',
        readonly=True)
    last_sell_date = Field(
        attribute='last_sell_date',
        column_name='تاریخ آخرین فروش',
        readonly=True)
    manager_full_name = Field(
        attribute='manager_full_name',
        column_name='نام و نام خانوادگی مدیر فروشگاه',
        readonly=True)
    manager_mobile_number = Field(
        attribute='manager_mobile_number',
        column_name='شماره مدیر فروشگاه',
        readonly=True)
    manager_last_login = Field(
        attribute='manager_last_login',
        column_name='تاریخ آخرین ورود مدیر فروشگاه',
        readonly=True)

    class Meta:
        model = Shop
        fields = (
            'title',
            'slug',
            'date_created',
            'date_updated',
            'state',
            'city',
            'products_count',
            'total_sell',
            'last_sell_date',
            'manager_full_name',
            'manager_mobile_number',
            'manager_last_login')

    def get_queryset(self):
        return Shop.objects.select_related('FK_ShopManager')
