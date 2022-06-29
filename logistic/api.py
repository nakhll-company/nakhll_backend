from django.utils.translation import ugettext as _
from rest_framework import permissions, viewsets, mixins
from logistic.models import Address, ShopLogisticUnit, ShopLogisticUnitConstraint, ShopLogisticUnitCalculationMetric
from logistic.serializers import (
    AddressReadSerializer,
    AddressWriteSerializer,
    ShopLogisticUnitCalculationMetricSerializer,
    ShopLogisticUnitConstraintReadSerializer,
    ShopLogisticUnitConstraintWriteSerializer,
    ShopLogisticUnitFullSerializer)
from logistic.permissions import IsAddressOwner, IsShopOwner
from nakhll_market.models import Shop

class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressReadSerializer
    permission_classes = [IsAddressOwner, permissions.IsAuthenticated ]
    lookup_field = 'id'

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return AddressReadSerializer
        else:
            return AddressWriteSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ShopLogisticUnitViewSet(viewsets.ModelViewSet):
    serializer_class = ShopLogisticUnitFullSerializer
    permission_classes = [permissions.IsAuthenticated, IsShopOwner]
    lookup_field = 'id'

    def get_shop(self):
        shop_slug = self.request.GET.get('shop')
        try:
            return Shop.objects.get(Slug=shop_slug)
        except Shop.DoesNotExist:
            return None

    def get_queryset(self):
        queryset = ShopLogisticUnit.objects.filter(shop__FK_ShopManager=self.request.user)
        shop = self.get_shop()
        if shop:
            queryset = queryset.filter(shop=shop)
        return queryset.select_related('constraint', 'calculation_metric')

    def perform_create(self, serializer):
        slu = serializer.save()
        ShopLogisticUnitConstraint.objects.create(shop_logistic_unit=slu)
        ShopLogisticUnitCalculationMetric.objects.create(shop_logistic_unit=slu)
    

class ShopLogisticUnitConstraintViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.UpdateModelMixin):
    permission_classes = [permissions.IsAuthenticated, IsShopOwner]
    lookup_field = 'id'

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ShopLogisticUnitConstraintReadSerializer
        return ShopLogisticUnitConstraintWriteSerializer

    def get_queryset(self):
        shop_logistic_unit_id = self.request.GET.get('id')
        queryset = ShopLogisticUnitConstraint.objects.filter(shop_logistic_unit__shop__FK_ShopManager=self.request.user)
        if shop_logistic_unit_id:
            return queryset.filter(shop_logistic_unit__id=shop_logistic_unit_id)
        return queryset             
        


class ShopLogisticUnitCalculationMetricViewSet(viewsets.GenericViewSet,
                                             mixins.UpdateModelMixin,
                                             mixins.RetrieveModelMixin):
    serializer_class = ShopLogisticUnitCalculationMetricSerializer
    permission_classses = [permissions.IsAuthenticated, IsShopOwner]
    lookup_field = 'id'

    def get_queryset(self):
        return ShopLogisticUnitCalculationMetric.objects.filter(
            shop_logistic_unit__shop__FK_ShopManager=self.request.user
        )
  