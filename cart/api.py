from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from cart.managers import CartManager
from django.utils.translation import ugettext as _
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from nakhll_market.models import ProductManager
from cart.models import Cart, CartItem
from cart.serializers import (CartSerializer, CartItemSerializer,
                              CartWriteSerializer)
from cart.utils import get_user_or_guest
from cart.permissions import IsCartOwner, IsCartItemOwner
from payoff.exceptions import (NoAddressException, InvoiceExpiredException,
                               InvalidInvoiceStatusException, NoItemException,
                               OutOfPostRangeProductsException)
from logistic.interfaces import LogisticUnitInterface


class UserCartViewSet(viewsets.GenericViewSet):
    serializer_class = CartSerializer
    permission_classes = [IsCartOwner, ]

    def get_object(self):
        user, guid = get_user_or_guest(self.request)
        if user or guid:
            'TODO: return CartManager._get_user_cart(user, guid)'
            return CartManager.user_active_cart(user, guid)
        return None

    @action(detail=False, methods=['GET'], name='View current user active cart')
    def me(self, request):
        cart = self.get_object()
        serializer = self.get_serializer(cart)
        response = Response(serializer.data)
        self._delete_guid_cookie(response)
        return response

    def _delete_guid_cookie(self, response):
        if self.request.user and self.request.user.is_authenticated:
            response.delete_cookie('guest_unique_id')
        return response

    @action(methods=['PATCH'], detail=False)
    def set_address(self, request):
        # TODO: do I raise error if address is not valid?
        # TODO: do I clear the cart if no address is available?
        cart = self.get_object()
        serializer = CartWriteSerializer(instance=cart, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        lui = self.get_logistic_details(cart)
        cart.logistic_details = lui.as_dict()
        cart.save()
        return Response(lui.as_dict(), status=status.HTTP_200_OK)

    def get_logistic_details(self, cart):
        # if not self.address:
        # raise ValidationError(_('آدرس سفارش را وارد کنید'))
        lui = LogisticUnitInterface(cart)
        lui.generate_logistic_unit_list()
        return lui

    @action(methods=['PATCH'], detail=False)
    def set_coupon(self, request):
        ''' Verify and calculate user coupon and return discount amount
        
            ensure that user address is filled.
            Send this invoice with coupon to coupon app and get amount of 
            discount that should applied, or errors if there is any. Coupon
            should be applied and saved in invoice for future reference
        '''
        cart = self.get_object()
        serializer = CartWriteSerializer(instance=cart, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        coupon = serializer.validated_data.get('coupon')
        if coupon.is_valid(cart):
            serializer.save()
            cart.coupons.add(coupon)
        return Response({'coupon': coupon.code, 'result': coupon.final_price, 'errors': coupon.errors},
                        status=status.HTTP_200_OK)

    @action(methods=['PATCH'], detail=False)
    def unset_coupon(self, request):
        ''' Unset coupon from cart'''
        cart = self.get_object()
        serializer = CartWriteSerializer(instance=cart, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        coupon = serializer.validated_data.get('coupon')
        if coupon not in cart.coupons.all():
            return Response({'coupon': 'کوپن تخفیف وارد شده نامعتبر است'}, status=status.HTTP_400_BAD_REQUEST)
        cart.coupons.remove(coupon)
        serializer.save()
        return Response({'result': 0}, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False)
    def pay(self, request):
        ''' Convert cart to invoice and send to payment app '''
        cart = self.get_object()
        try:
            invoice = cart.convert_to_invoice()
            return invoice.send_to_payment()
        except NoItemException:
            return Response({'error': 'سبد خرید شما خالی است. لطفا سبد خرید خود را تکمیل کنید'},
                            status=status.HTTP_400_BAD_REQUEST)
        except NoAddressException:
            return Response({'error': 'آدرس خریدار را تکمیل کنید'}, status=status.HTTP_400_BAD_REQUEST)
        except InvoiceExpiredException:
            return Response({'error': 'فاکتور منقضی شده است'}, status=status.HTTP_400_BAD_REQUEST)
        except InvalidInvoiceStatusException:
            return Response({'error': 'فاکتور در حال حاضر قابل پرداخت نیست'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            return Response({'error': str(ex)}, status=status.HTTP_400_BAD_REQUEST)


class UserCartItemViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin):
    serializer_class = CartItemSerializer
    permission_classes = [IsCartItemOwner, ]

    def get_object(self):
        try:
            cart_item = CartItem.objects.get(pk=self.kwargs['pk'])
            self.check_object_permissions(self.request, cart_item)
            return cart_item
        except CartItem.DoesNotExist:
            raise ValidationError({'error': ['محصول با این شناسه در سبد خرید شما وجود ندارد']})

    def create(self, request, *args, **kwargs):
        cart = self.get_cart()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(cart=cart)
        cart_serializer = CartSerializer(cart)
        headers = self.get_success_headers(serializer.data)
        response = Response(cart_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        cart.reset_address()
        cart.reset_coupons()
        return self.append_cookie(response, cart)

    @action(detail=True, methods=['DELETE'], name='Remove item from active cart', url_path='reduce')
    def reduce_item(self, request, pk):
        cart = self.get_cart()
        cart_item = self.get_object()
        cart_item.reduce_count()
        cart_serializer = CartSerializer(cart_item.cart)
        cart.reset_address()
        cart.reset_coupons()
        return Response(cart_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['DELETE'], name='Delete whole cart item', url_path='delete')
    def delete_item(self, request, pk):
        cart = self.get_cart()
        cart_item = self.get_object()
        cart_item.delete()
        cart_serializer = CartSerializer(cart_item.cart)
        cart.reset_address()
        cart.reset_coupons()
        return Response(cart_serializer.data, status=status.HTTP_200_OK)

    def append_cookie(self, response, cart):
        if not self.request.COOKIES.get('guest_unique_id'):
            response.set_cookie('guest_unique_id', cart.guest_unique_id, max_age=60 * 60 * 24 * 365)
        return response

    def get_cart(self):
        '''
       TODO: is it necessary after revert
            """Get user cart from request. It may be guest or user cart"""
            user, guid = get_user_or_guest(self.request)
            if user or guid:
                return CartManager._get_user_cart(user, guid)
            return None
        '''
        return Cart.get_user_cart(self.request)
