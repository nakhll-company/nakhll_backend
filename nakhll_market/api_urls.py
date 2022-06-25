from django.urls import re_path, include, path
from nakhll_market.api import (
    AllShopSettings, CategoryViewSet, GroupProductCreateExcel, GroupProductUndo,
    PublicShopsViewSet, UserImagesViewSet, GroupProductUpdateExcel,
    ImageShopSettings, LastCreatedDiscountedProductsViewSet,
    LastCreatedProductsViewSet, MostDiscountPrecentageProductsViewSet,
    MostSoldProduct, ShopMultipleUpdateInventory, ShopMultipleUpdatePrice,
    CategoryViewSet, StateFullViewSet, UserProfileViewSet, GetShop,
    UserOrderHistory, GetShopList, ShopOwnerProductViewSet,
    ProductsInSameFactorViewSet, SliderViewSet, MostSoldShopsViewSet,
    RandomShopsViewSet, RandomProductsViewSet, ProductsViewSet, CreateShop,
    GetShopWithSlug, CheckShopSlug, CheckProductSlug, ShopProductsViewSet,
    ProductCommentsViewSet, ProductRelatedItemsViewSet, ProductBannerViewSet,
    AddImagesToProduct, ProductDetailsViewSet, LandingPageSchemaViewSet,
    ShopPageSchemaViewSet, ShopsStatisticView, TagsOwnerViewSet,
    DeleteShopImage)
from rest_framework import routers

app_name = 'nakhll_market'

landing_router = routers.DefaultRouter()
landing_router.register(r'sliders', SliderViewSet, basename="sliders")
landing_router.register(
    r'last-created-products',
    LastCreatedProductsViewSet,
    basename="last-created-products")
landing_router.register(
    r'last-created-discounted-products',
    LastCreatedDiscountedProductsViewSet,
    basename="last-created-discounted-products")
landing_router.register(
    r'most-discount-prec-products',
    MostDiscountPrecentageProductsViewSet,
    basename="most-discount-prec-products")
landing_router.register(
    r'most-sold-shops',
    MostSoldShopsViewSet,
    basename="most-sold-shops")
landing_router.register(
    r'random-shops',
    RandomShopsViewSet,
    basename="random-shops")
landing_router.register(
    r'random-products',
    RandomProductsViewSet,
    basename="random-products")
landing_router.register(
    r'shop_products',
    ShopProductsViewSet,
    basename="shop_products")
landing_router.register(
    r'schema',
    LandingPageSchemaViewSet,
    basename="landing_page_schema")

product_page_router = routers.DefaultRouter()
product_page_router.register(r'', ProductsViewSet, basename="all_products")
product_page_router.register(
    r'details',
    ProductDetailsViewSet,
    basename="details")
product_page_router.register(
    r'comments',
    ProductCommentsViewSet,
    basename="comments")
product_page_router.register(
    r'related_products',
    ProductRelatedItemsViewSet,
    basename="related_products")

util_router = routers.DefaultRouter()
util_router.register(r'states', StateFullViewSet, basename="states")
util_router.register(r'shops', PublicShopsViewSet, basename="shops")

profile_router = routers.DefaultRouter()
profile_router.register(r'', UserProfileViewSet, basename="profile")
profile_router.register(r'orders', UserOrderHistory, basename="orders")
profile_router.register(r'images', UserImagesViewSet, basename="user_images")

product_banners_router = routers.DefaultRouter()
product_banners_router.register(
    r'',
    ProductBannerViewSet,
    basename="product_banners")


shop_owner_router = routers.DefaultRouter()
shop_owner_router.register(
    r'products',
    ShopOwnerProductViewSet,
    basename="products")
shop_owner_router.register(r'tags', TagsOwnerViewSet, basename="tags")

categories_router = routers.DefaultRouter()
categories_router.register(r'', CategoryViewSet, basename="categories")

urlpatterns = [
    path('landing/', include(landing_router.urls)),
    path('products/', include(product_page_router.urls)),
    path('product/banners/', include(product_banners_router.urls)),
    path('product-page/', include(product_page_router.urls)),
    path('product-page/same-factor/<uuid:ID>/', ProductsInSameFactorViewSet.as_view()),
    path('shop/create/', CreateShop.as_view()),
    path('shop/<Slug>/', GetShop.as_view({'get': 'retrieve'})),
    path('shop/<shop_slug>/', include(shop_owner_router.urls)),

    path('util/', include(util_router.urls)),

    path('shop/', GetShopWithSlug.as_view()),
    path('shops/', GetShopList.as_view({'get': 'list'})),
    path('shop/<shop_slug>/settings/image/', DeleteShopImage.as_view()),
    path('shop/<shop_slug>/settings/', AllShopSettings.as_view()),
    # path('shop/<shop_slug>/settings/bank_account/', BankAccountShopSettings.as_view()),
    # path('shop/<shop_slug>/settings/social_media/', SocialMediaShopSettings.as_view()),
    path('shop/<shop_slug>/settings/avatar/', ImageShopSettings.as_view()),
    path('shop/check/', CheckShopSlug.as_view()),
    path('shop/multiple-update/price/', ShopMultipleUpdatePrice.as_view()),
    path('shop/multiple-update/inventory/', ShopMultipleUpdateInventory.as_view()),
    path('shop/schema/<shop_id>/', ShopPageSchemaViewSet.as_view()),

    path('product/check/', CheckProductSlug.as_view()),
    path('product/images/', AddImagesToProduct.as_view()),
    path('product/group-create/<shop_slug>/', GroupProductCreateExcel.as_view()),
    path('product/group-update/<shop_slug>/', GroupProductUpdateExcel.as_view()),
    path('product/group-undo/<shop_slug>/', GroupProductUndo.as_view()),
    path('product/most-sold/', MostSoldProduct.as_view()),
    
    path('profile/', include(profile_router.urls)),

    path('categories/', include(categories_router.urls)),
    path('statistics/shop/', ShopsStatisticView.as_view()),

    # path('torob/products/', TorobAllProducts.as_view()),
]
