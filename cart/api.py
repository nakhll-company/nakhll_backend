from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from cart.managers import CartManager
from django.utils.translation import ugettext as _
from rest_framework import permissions, viewsets, mixins
from nakhll.authentications import CsrfExemptSessionAuthentication
from nakhll_market.models import ProductManager
from cart.models import Cart, CartItem, CartTransmission
from cart.serializers import CartSerializer, CartItemSerializer, CartTransmissionSerializer
from cart.utils import get_user_or_guest
from cart.permissions import IsCartOwner, IsCartItemOwner


class UserCartViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    serializer_class = CartSerializer
    authentication_classes = [CsrfExemptSessionAuthentication, ]
    permission_classes = [IsCartOwner, ]

    def get_queryset(self):
        user, guid = get_user_or_guest(self.request)
        return CartManager.user_active_cart(user, guid)

    def get_object(self):
        user, guid = get_user_or_guest(self.request)
        return CartManager.user_active_cart(user, guid)

    @action(detail=False, methods=['POST', 'GET'], name='Send active cart to accounting')
    def send_to_accounting(self, request):
        cart = self.get_object()
        is_differ, old, new = cart.get_diffrences()
        if is_differ:
            raise ValidationError('Differ')
        
    @action(detail=False, methods=['GET'], name='View current user active cart')
    def my(self, request):
        cart = self.get_object()
        serializer = self.get_serializer(cart)
        return Response(serializer.data)
        



class UserCartItemViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        user, guid = get_user_or_guest(self.request)
        return CartItem.objects.user_cartitems(user, guid)


    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)




    def perform_create(self, serializer):
        user, guid = get_user_or_guest(self.request)
        product = serializer.validated_data.get('product')
        count = serializer.validated_data.get('count')
        if not ProductManager.is_product_available(product, count):
            raise ValidationError(_('محصول در دسترس نیست و یا به تعداد کافی از این محصول در انبار وجود ندارد'))
        active_cart = CartManager.user_active_cart(user, guid)
        product_jsonify = ProductManager.jsonify_product(product)
        serializer.save(cart=active_cart, product_last_known_state=product_jsonify)

    def perform_update(self, serializer):
        # TODO: check if permissions are correct
        user, guid = get_user_or_guest(self.request)
        product = serializer.validated_data.get('product')
        count = serializer.validated_data.get('count')
        if not ProductManager.is_product_available(product, count):
            raise ValidationError(_('محصول در دسترس نیست و یا به تعداد کافی از این محصول در انبار وجود ندارد'))
        product_jsonify = ProductManager.jsonify_product(product)
        serializer.save(product_last_known_state=product_jsonify)

    serializer_class = CartItemSerializer
    authentication_classes = [CsrfExemptSessionAuthentication, ]
    permission_classes = [IsCartItemOwner, ]


class CartTransmissionViewSet(viewsets.ModelViewSet):
    serializer_class = CartTransmissionSerializer
    authentication_classes = [CsrfExemptSessionAuthentication, ]
    permission_classes = [IsCartItemOwner, ]
    queryset = CartTransmission.objects.all()

    def perform_create(self, serializer):
        serializer.save()


# 1- there is an api to send cart to accounting, which in first of it I should check all items in factor
# 2- Should I send active cart to accounting or accounting ask for it? 
