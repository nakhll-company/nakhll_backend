from typing import Dict, Optional
from import_export.admin import ExportActionMixin
from django.contrib import admin
from django.http import HttpRequest, HttpResponse
from django.utils.timezone import localtime
from django.contrib import messages
from django.utils.translation import ngettext
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.auth.models import Permission, User
from django.db.models import Count
from nakhll import utils
from nakhll_market.models import (
    LandingPageSchema,
    Category,
    ShopPageSchema,
    LandingImage,
    LandingPage,
    Shop,
    Product,
    ProductBanner,
    Profile,
    Alert,
    DashboardBanner,
    Slider,
    Tag,
    ProductTag)
from nakhll_market.resources import ProfileResource


admin.site.site_header = 'مدیریت بازار نخل'

# enable django permission setting in admin panel to define custom permissions
admin.site.register(Permission)

ModelAdmin.construct_change_message = (
    lambda self, request, form, formsets, add:
    utils.construct_change_message(request, form, formsets, add)
)


class ProfileHasShopFilter(admin.SimpleListFilter):
    title = 'حجره'
    parameter_name = 'shop_manager'

    def lookups(self, request, model_admin):
        return [
            ('yes', 'دارد'),
            ('no', 'ندارد'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.have_shop()

        if self.value() == 'no':
            return queryset.have_not_shop()

# profile admin panel
@admin.register(Profile)
class ProfileAdmin(ExportActionMixin, admin.ModelAdmin):
    list_display = ('FK_User', 'first_name', 'last_name', 'date_joined')
    readonly_fields = ('date_joined', 'FK_User', 'MobileNumber')
    list_filter = (
        'FK_User__date_joined', ProfileHasShopFilter,)
    ordering = ('-FK_User__date_joined',)
    fields = (
        'FK_User',
        'MobileNumber',
        'BrithDay',
        'Image',
        'ImageNationalCard',
    )
    search_fields = (
        'MobileNumber__icontains',
        'FK_User__first_name__icontains',
        'FK_User__last_name__icontains')
    resource_class = ProfileResource

    def get_queryset(self, request: HttpRequest):
        return super().get_queryset(request).select_related('FK_User')\
            .shop_count()

    @admin.display(ordering='FK_User__date_joined',
                   description='تاریخ عضویت')
    def date_joined(self, obj):
        return obj.date_joined

    @admin.display(ordering='FK_User__first_name', description='نام')
    def first_name(self, obj):
        return obj.user.first_name

    @admin.display(ordering='FK_User__last_name', description='نام خانوادگی')
    def last_name(self, obj):
        return obj.user.last_name

# -------------------------------------------------
# market admin panel


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = (
        'Title',
        'Slug',
        'City',
        'State',
        'Point',
        'DateCreate',
        'Available',
        'Publish',
    )
    list_filter = (
        'City',
        'State',
        'Publish',
        'Available',
        'DateCreate',
        'DateUpdate')
    search_fields = ('Title', 'Slug')
    ordering = ['ID', 'DateCreate', 'DateUpdate']
    raw_id_fields = ('FK_ShopManager',)

    def DateCreate(self, obj):
        return localtime(obj.DateCreate).strftime('%Y-%m-%d %H:%M:%S')

    def DateUpdate(self, obj):
        return localtime(obj.DateUpdate).strftime('%Y-%m-%d %H:%M:%S')


class ProductBannerInline(admin.StackedInline):
    model = ProductBanner
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'Title',
        'Slug',
        'Bio',
        'Price',
        'Status',
        'DateCreate',
        'Publish')
    list_filter = ('Status', 'Publish', 'Available', 'DateCreate', 'DateUpdate')
    search_fields = ('Title', 'Slug', 'Description', 'Bio', 'Story')
    ordering = ['ID', 'DateCreate', 'DateUpdate']
    inlines = [ProductBannerInline, ]
    actions = ["un_publish_product", "publish_product"]

    @admin.action(description='از حالت انتشار خارج کن', )
    def un_publish_product(self, request, queryset):
        updated = queryset.update(Publish=False)
        self.message_user(request, ngettext(
            '%d محصول از انتشار خارج شد',
            '%d  محصول از انتشار خارج شد',
            updated,
        ) % updated, messages.SUCCESS)

    @admin.action(description='منتشر کن', )
    def publish_product(self, request, queryset):
        updated = queryset.update(Publish=True)
        self.message_user(request, ngettext(
            '%d محصول منتشر شد',
            '%d محصول منتشر شد',
            updated,
        ) % updated, messages.SUCCESS)

    def DateCreate(self, obj):
        return localtime(obj.DateCreate).strftime('%Y-%m-%d %H:%M:%S')

    def DateUpdate(self, obj):
        return localtime(obj.DateUpdate).strftime('%Y-%m-%d %H:%M:%S')

    def change_view(
            self, request: HttpRequest, object_id: str, form_url: str = '',
            extra_context: Optional[Dict[str, bool]] = None) -> HttpResponse:
        if request.user.groups.filter(name='Photo-compress').exists():
            self.fields = ('Image', 'NewImage')
        else:
            self.fields = None
        return super().change_view(request, object_id,
                                   form_url=form_url, extra_context=extra_context)


# -------------------------------------------------

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'order',
        'slug',
        'description',
        'parent',
        'available')
    list_filter = ('parent', 'available')
    ordering = ('-parent', 'id',)


# -------------------------------------------------
# Alert admin panel
@admin.register(Alert)
class AlertAdmin(ModelAdmin):
    list_display = ('Part', 'Slug', 'Seen', 'DateCreate', 'Description',)
    list_filter = ('Seen', 'Status', 'DateCreate', 'DateCreate', 'DateUpdate')
    search_fields = ('FK_Field', 'Description', 'Content',)
    ordering = ['id', 'DateCreate', ]

    def DateCreate(self, obj):
        return localtime(obj.DateCreate).strftime('%Y-%m-%d %H:%M:%S')

    def DateUpdate(self, obj):
        return localtime(obj.DateUpdate).strftime('%Y-%m-%d %H:%M:%S')


@admin.register(ProductBanner)
class ProductBanner(ModelAdmin):
    list_display = ('FK_Product', 'Title', 'DateCreate', 'DateUpdate')
    list_filter = ('FK_Product', 'Title', 'DateCreate', 'DateUpdate')
    search_fields = ('FK_Product__Title',)
    ordering = ('DateCreate',)

    def DateCreate(self, obj):
        return localtime(obj.DateCreate).strftime('%Y-%m-%d %H:%M:%S')

    def DateUpdate(self, obj):
        return localtime(obj.DateUpdate).strftime('%Y-%m-%d %H:%M:%S')


@admin.register(DashboardBanner)
class DashboardBannerAdmin(admin.ModelAdmin):
    list_display = (
        'image',
        'url',
        'staff_user',
        'created_datetime',
        'publish_status')

    list_filter = ('staff_user', 'created_datetime', 'publish_status')
    search_fields = ('url',)
    ordering = ['id', 'created_datetime', 'publish_status']

    def created_datetime(self, obj):
        return localtime(obj.created_datetime).strftime('%Y-%m-%d %H:%M:%S')
    # inlines=[AttrProductInline, ProductBannerInline, ProductMovieInline]


@admin.register(LandingPageSchema)
class LandingPageSchemaAdmin(ModelAdmin):
    list_display = (
        'component_type',
        'title',
        'subtitle',
        'image',
        'url',
        'data',
        'order',
        'publish_status')
    list_filter = ('publish_status', 'created_datetime', 'order')
    search_fields = ('title', 'component_type', 'subtitle', 'url', 'data')
    ordering = ['publish_status', 'created_datetime']

    def created_datetime(self, obj):
        return localtime(obj.created_datetime).strftime('%Y-%m-%d %H:%M:%S')


@admin.register(ShopPageSchema)
class ShopPageSchemaAdmin(ModelAdmin):
    list_display = (
        'shop',
        'component_type',
        'title',
        'subtitle',
        'image',
        'url',
        'data',
        'order',
        'publish_status')
    list_filter = ('shop', 'publish_status', 'created_datetime', 'order')
    search_fields = (
        'shop',
        'title',
        'component_type',
        'subtitle',
        'url',
        'data')
    ordering = ['publish_status', 'created_datetime']

    def created_datetime(self, obj):
        return localtime(obj.created_datetime).strftime('%Y-%m-%d %H:%M:%S')


@admin.register(LandingPage)
class LandingPageAdmin(ModelAdmin):
    list_display = ('slug', 'status', 'staff', 'created_at', 'updated_at')
    list_filter = ('status',)
    search_fields = ('slug', 'page_data')
    ordering = ['created_at']

    def created_datetime(self, obj):
        return localtime(obj.created_datetime).strftime('%Y-%m-%d %H:%M:%S')


@admin.register(LandingImage)
class LandingImageAdmin(ModelAdmin):
    list_display = (
        'image',
        'staff',
        'created_at',
        'updated_at',
        'landing_page')
    list_filter = ('landing_page',)
    ordering = ['created_at']

    def created_datetime(self, obj):
        return localtime(obj.created_datetime).strftime('%Y-%m-%d %H:%M:%S')


@admin.register(Slider)
class SliderAdmin(ModelAdmin):
    list_display = ('Title', 'Description', 'Location', 'DateCreate', 'Publish')
    list_filter = ('Location', 'DateCreate', 'DtatUpdate', 'Publish')
    ordering = ['DateCreate', 'id', 'Publish', 'Title', 'Location']

    def DateCreate(self, obj):
        return localtime(obj.DateCreate).strftime('%Y-%m-%d %H:%M:%S')

    def DtatUpdate(self, obj):
        return localtime(obj.DtatUpdate).strftime('%Y-%m-%d %H:%M:%S')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'shop']
    list_filter = ['shop']
    search_fields = ['name']


@admin.register(ProductTag)
class ProductTagAdmin(admin.ModelAdmin):
    list_display = ['id', 'tag', 'product']
    search_fields = ['tag__name']
    autocomplete_fields = ['product', 'tag']
