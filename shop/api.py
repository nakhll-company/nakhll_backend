from django.http.response import Http404
from django.utils import timezone
from django.utils.translation import ugettext as _
from rest_framework import status, mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from django_filters import rest_framework as filters
from nakhll.utils import excel_response
from invoice.filters import InvoiceFilter
from invoice.models import Invoice
from invoice.serializers import InvoiceProviderRetrieveSerializer
from nakhll_market.models import Shop
from nakhll_market.paginators import StandardPagination
from shop.resources import ProductResource
from .models import ShopAdvertisement, ShopFeature, ShopFeatureInvoice, ShopLanding, PinnedURL
from .serializers import (
    ShopAdvertisementSerializer,
    ShopFeatureDetailSerializer,
    ShopFeatureInvoice,
    ShopFeatureInvoiceSerializer,
    ShopFeatureInvoiceWriteSerializer,
    ShopFeatureSerializer,
    ShopLandingDetailsSerializer,
    ShopLandingSerializer,
    UserPinnedURLSerializer,
)
from .permissions import IsInvoiceProvider, IsShopOwner, IsPinnedURLOwner, ShopLandingPermission
from .mixins import MultipleFieldLookupMixin


class ExtendedPagination(StandardPagination):
    page_size = 200


class ShopFeatureViewSet(viewsets.GenericViewSet,
                         mixins.RetrieveModelMixin, mixins.ListModelMixin):
    queryset = ShopFeature.objects.published()
    serializer_class = ShopFeatureSerializer
    permission_classes = [permissions.AllowAny, ]

    def get_serializer_class(self):
        if self.action == 'list':
            return ShopFeatureSerializer
        else:
            return ShopFeatureDetailSerializer


class ShopFeatureInvoiceViewSet(
        viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.DestroyModelMixin):
    permission_classes = [permissions.IsAuthenticated, IsShopOwner]
    queryset = ShopFeatureInvoice.objects.all()
    lookup_field = 'id'

    def get_serializer_class(self):
        if self.action == 'create':
            return ShopFeatureInvoiceWriteSerializer

    @action(detail=False, methods=['get'],
            url_path='(?P<shop_slug>[^/.]+)/history')
    def shop_feature_invoices_history(self, request, shop_slug):
        feature_id = request.query_params.get('feature')
        shop = self.get_shop(shop_slug)
        invoices = ShopFeatureInvoice.objects.filter(shop=shop)
        if feature_id:
            invoices = invoices.filter(feature__id=feature_id)
        serializer = ShopFeatureInvoiceSerializer(invoices, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def activate_demo(self, request):
        serializer = ShopFeatureInvoiceWriteSerializer(data=request.data)
        if serializer.is_valid(is_demo=True):
            feature = serializer.validated_data.get('feature')
            invoice = serializer.save(
                is_demo=True,
                status=ShopFeatureInvoice.ShopFeatureInvoiceStatuses.COMPLETED,
                bought_price_per_unit=feature.price_per_unit_with_discount,
                bought_unit=feature.unit, unit_count=1,
                start_datetime=timezone.now())
            invoice.save_expire_datetime()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        feature = serializer.validated_data.get('feature')
        serializer.save(
            is_demo=False,
            status=ShopFeatureInvoice.ShopFeatureInvoiceStatuses.AWAIT_PAYMENT,
            bought_price_per_unit=feature.price_per_unit_with_discount,
            bought_unit=feature.unit,
            unit_count=1)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status != ShopFeatureInvoice.ShopFeatureInvoiceStatuses.AWAIT_PAYMENT:
            return Response(
                {'error': 'شما نمی‌توانید این فاکتور را پاک کنید'},
                status=status.HTTP_400_BAD_REQUEST)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def pay(self, request, id=None):
        invoice = self.get_object()
        if invoice.status != ShopFeatureInvoice.ShopFeatureInvoiceStatuses.AWAIT_PAYMENT:
            return Response(
                {'error': 'شما نمی‌توانید این فاکتور را پرداخت کنید'},
                status=status.HTTP_400_BAD_REQUEST)
        return invoice.send_to_payment()

    def get_shop(self, shop_slug):
        try:
            shop = Shop.objects.get(Slug=shop_slug)
            self.check_object_permissions(self.request, shop)
            return shop
        except Shop.DoesNotExist as ex:
            raise Http404


class ShopLandingViewSet(
        MultipleFieldLookupMixin, mixins.RetrieveModelMixin, mixins.ListModelMixin,
        mixins.CreateModelMixin, mixins.DestroyModelMixin, mixins.UpdateModelMixin,
        viewsets.GenericViewSet):
    queryset = ShopLanding.objects.all()
    permission_classes = [
        permissions.IsAuthenticated,
        IsShopOwner,
        ShopLandingPermission]
    lookup_fields = ['shop__Slug', 'pk']

    def get_serializer_class(self):
        if self.action == 'list':
            return ShopLandingSerializer
        else:
            return ShopLandingDetailsSerializer

    def get_shop(self):
        shop_slug = self.kwargs.get('shop__Slug')
        return get_object_or_404(Shop, Slug=shop_slug,
                                 FK_ShopManager=self.request.user)

    def get_queryset(self):
        return super().get_queryset().filter(
            shop__FK_ShopManager=self.request.user, **self.kwargs)

    @action(detail=True, methods=['get'], )
    def activate_landing(self, request, shop__Slug, pk=None):
        shop_landing = self.get_object()
        ShopLanding.objects.deactivate_all_landing_for_shop(shop_landing.shop)
        shop_landing.status = ShopLanding.Statuses.ACTIVE
        shop_landing.save()
        return Response(status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], )
    def deactivate_landing(self, request, shop__Slug, pk=None):
        shop_landing = self.get_object()
        shop_landing.status = ShopLanding.Statuses.INACTIVE
        shop_landing.save()
        return Response(status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        shop = self.get_shop()
        serializer.save(shop=shop)

    def perform_update(self, serializer):
        shop = self.get_shop()
        serializer.save(shop=shop)


class PinnedURLViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin,
                       mixins.ListModelMixin, mixins.CreateModelMixin,
                       mixins.DestroyModelMixin):
    queryset = PinnedURL.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsPinnedURLOwner]
    serializer_class = UserPinnedURLSerializer

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ShopViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated, IsShopOwner]
    queryset = Shop.objects.all()
    lookup_field = 'Slug'

    @action(detail=True, methods=['get'])
    def products_as_excel(self, request, Slug=None):
        shop = self.get_object()
        return excel_response(ProductResource, shop.products, 'products')


class ShopAdvertisementViewSet(
        viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.UpdateModelMixin):
    queryset = ShopAdvertisement.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsShopOwner]
    serializer_class = ShopAdvertisementSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        return super().get_queryset().filter(shop__FK_ShopManager=self.request.user)

    def get_object(self):
        shop_slug = self.kwargs.get(self.lookup_field, '')
        shop = get_object_or_404(Shop, Slug=shop_slug)
        if not hasattr(shop, 'advertisement'):
            ads = ShopAdvertisement.objects.create(shop=shop)
        else:
            ads = shop.advertisement
        self.check_object_permissions(self.request, ads)
        return ads


class ShopInvoicesViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin,
                          mixins.ListModelMixin, mixins.UpdateModelMixin):
    permission_classes = [
        permissions.IsAuthenticated,
        IsShopOwner,
        IsInvoiceProvider]
    serializer_class = InvoiceProviderRetrieveSerializer
    lookup_field = 'id'
    filter_class = InvoiceFilter
    filter_backends = (filters.DjangoFilterBackend,)
    pagination_class = ExtendedPagination

    def get_queryset(self):
        shop_slug = self.kwargs.get('shop__Slug')
        shop = get_object_or_404(Shop, Slug=shop_slug)
        self.check_object_permissions(self.request, shop)
        return Invoice.objects.shop_invoices(shop_slug)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
