from import_export.resources import ModelResource
from import_export.fields import Field
from nakhll_market.models import Product


class ProductResource(ModelResource):
    title = Field(
        attribute='title',
        column_name='عنوان',
        readonly=True
    )
    barcode = Field(
        attribute='barcode',
        column_name='بارکد',
        readonly=True
    )
    price = Field(
        attribute='price',
        column_name='قیمت با تخفیف',
        readonly=True
    )
    old_price = Field(
        attribute='old_price',
        column_name='قیمت بدون تخفیف',
        readonly=True
    )
    inventory = Field(
        attribute='inventory',
        column_name='موجودی',
        readonly=True
    )
    net_weight = Field(
        attribute='net_weight',
        column_name='وزن خالص',
        readonly=True
    )
    weight_with_packing = Field(
        attribute='weight_with_packing',
        column_name='وزن با بسته بندی',
        readonly=True
    )
    category_id = Field(
        attribute='category_id',
        column_name='دسته بندی',
        readonly=True
    )
    publish = Field(
        attribute='publish',
        column_name='وضعیت انتشار',
        readonly=True
    )

    class Meta:
        model = Product
