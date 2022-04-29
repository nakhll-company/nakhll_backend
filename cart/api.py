from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from logistic.interfaces import LogisticUnitInterface
from payoff.exceptions import (InvalidInvoiceStatusException,
                               InvoiceExpiredException, NoAddressException,
                               NoItemException)
from .managers import CartManager
from .models import Cart, CartItem
from .permissions import IsCartItemOwner, IsCartOwner
from .serializers import (CartItemSerializer, CartSerializer,
                          CartWriteSerializer)
from .utils import get_user_or_guest


class UserCartViewSet(viewsets.GenericViewSet):
    """Fetches rows from a Smalltable.

    Retrieves rows pertaining to the given keys from the Table instance
    represented by table_handle.  String keys will be UTF-8 encoded.

    Args:
      table_handle:
        An open smalltable.Table instance.
      keys:
        A sequence of strings representing the key of each table row to
        fetch.  String keys will be UTF-8 encoded.
      require_all_keys:
        If True only rows with values set for all keys will be returned.

    Returns:
      A dict mapping keys to the corresponding table row data
      fetched. Each row is represented as a tuple of strings. For
      example:

    .. code-block:: python

        {
            'Serak': ('Rigel VII', 'Preparer'),
            'Zim': ('Irk', 'Invader'),
            'Lrrr': ('Omicron Persei 8', 'Emperor')
        }

    Returned keys are always bytes.  If a key from the keys argument is
    missing from the dictionary, then that row was not found in the
    table (and require_all_keys must have been False).

    Raises:
      IOError: An error occurred accessing the smalltable.
    """
    serializer_class = CartSerializer
    permission_classes = [IsCartOwner, ]

    def get_object(self):
        user, guid = get_user_or_guest(self.request)
        if user or guid:
            return CartManager.get_user_cart(user, guid)
        return None

    @action(detail=False, name='View current user active cart', url_path='me')
    def my_cart(self, request):
        """View current user cart"""
        cart = self.get_object()
        serializer = self.get_serializer(cart)
        response = Response(serializer.data)
        self._delete_guid_cookie(response)
        return response

    def _delete_guid_cookie(self, response):
        """Delete guest_unique_id cookie

        Logged in users whom had a cart before logging in, has a guid in their
        cookie, which allows them to work with cart without logging in.
        After logging in, as we merge the cart with guid and user's own cart,
        we don't need that guid anymore, so we make sure that we delete that
        guid, so any new action with cart, will only affect user's own cart,
        not the guid cart.
        Note that, we only delete guid, if user has logged in.

        Args:
            response (HttpResponse): Response which may contains guid cookie

        Returns:
            HttpResponse: Response without guid cookie
        """
        if self.request.user and self.request.user.is_authenticated:
            response.delete_cookie('guest_unique_id')
        return response

    @action(methods=['PATCH'], detail=False)
    def set_address(self, request):
        """Set user address to cart

        User address will affect shipping price, and therefore, final invoice
        price. So, we calcuate shipping price, in this function too.
        """
        cart = self.get_object()
        serializer = CartWriteSerializer(
            instance=cart, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        lui = self._get_logistic_details(cart)
        cart.logistic_details = lui.as_dict()
        cart.save()
        return Response(lui.as_dict(), status=status.HTTP_200_OK)

    def _get_logistic_details(self, cart):
        lui = LogisticUnitInterface(cart)
        lui.generate_logistic_unit_list()
        return lui

    @action(methods=['PATCH'], detail=False)
    def set_coupon(self, request):
        """Verify and calculate user coupon and return discount amount

        Send this invoice with coupon to coupon app and get amount of
        discount that should applied, or errors if there is any. Coupon's
        will save in user cart, but they are not considered as applied coupons
        in user invoice. They will be applied to invoice after successful
        payment, or deleted from cart after failed payment.
        """
        cart = self.get_object()
        serializer = CartWriteSerializer(
            instance=cart, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        coupon = serializer.validated_data.get('coupon')
        if coupon.is_valid(cart):
            serializer.save()
            cart.coupons.add(coupon)
        return Response(
            {'coupon': coupon.code, 'result': coupon.final_price,
             'errors': coupon.errors},
            status=status.HTTP_200_OK)

    @action(methods=['PATCH'], detail=False)
    def unset_coupon(self, request):
        """Unset coupon from cart"""
        cart = self.get_object()
        serializer = CartWriteSerializer(
            instance=cart, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        coupon = serializer.validated_data.get('coupon')
        if coupon not in cart.coupons.all():
            return Response(
                {'coupon': 'کوپن تخفیف وارد شده نامعتبر است'},
                status=status.HTTP_400_BAD_REQUEST)
        cart.coupons.remove(coupon)
        serializer.save()
        return Response({'result': 0}, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False)
    def pay(self, request):
        """Convert cart to invoice and send to payment app

        Raises:
            NoItemException: There is no item in cart.
            NoAddressException: Address is not set for cart.
            InvoiceExpiredException: Invoice is expired. Invoices will
                expire after a period of time defined in settings as
                :attr:`nakhll.settings.INVOICE_EXPIRING_HOURS`
            InvalidInvoiceStatusException: Invoice status is not valid.
                Invoices should be in
                :attr:`invoice.models.Invoice.Statuses.AWAIT_PAYMENT`,
                any other status will raise this exception.
        """
        cart = self.get_object()
        try:
            invoice = cart.convert_to_invoice()
            return invoice.send_to_payment()
        except NoItemException:
            return Response({
                'error':
                'سبد خرید شما خالی است. لطفا سبد خرید خود را تکمیل کنید'},
                status=status.HTTP_400_BAD_REQUEST)
        except NoAddressException:
            return Response(
                {'error': 'آدرس خریدار را تکمیل کنید'},
                status=status.HTTP_400_BAD_REQUEST)
        except InvoiceExpiredException:
            return Response({'error': 'فاکتور منقضی شده است'},
                            status=status.HTTP_400_BAD_REQUEST)
        except InvalidInvoiceStatusException:
            return Response(
                {'error': 'فاکتور در حال حاضر قابل پرداخت نیست'},
                status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            return Response(
                {'error': str(ex)},
                status=status.HTTP_400_BAD_REQUEST)


class UserCartItemViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin):
    """Viewset for items in user cart"""

    serializer_class = CartItemSerializer
    permission_classes = [IsCartItemOwner, ]

    def get_object(self):
        try:
            cart_item = CartItem.objects.get(pk=self.kwargs['pk'])
            self.check_object_permissions(self.request, cart_item)
            return cart_item
        except CartItem.DoesNotExist as ex:
            raise ValidationError(
                {'error': ['محصول با این شناسه در سبد خرید شما وجود ندارد']}
            ) from ex

    def create(self, request, *args, **kwargs):
        cart = Cart.get_cart(request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(cart=cart)
        cart_serializer = CartSerializer(cart)
        headers = self.get_success_headers(serializer.data)
        response = Response(
            cart_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers)
        return self.append_cookie(response, cart)

    @action(detail=True, methods=['DELETE'],
            name='Remove item from active cart', url_path='reduce')
    def reduce_item(self, request, pk):
        """Reduce one item from cart, not removing it entirely"""
        cart = self.get_cart()
        cart_item = self.get_object()
        cart_item.reduce_count()
        cart_serializer = CartSerializer(cart_item.cart)
        cart.reset_address()
        cart.reset_coupons()
        return Response(cart_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['DELETE'],
            name='Delete whole cart item', url_path='delete')
    def delete_item(self, request, pk):
        """Remove item from cart, no matter how many times it was added"""
        cart = self.get_cart()
        cart_item = self.get_object()
        cart_item.delete()
        cart_serializer = CartSerializer(cart_item.cart)
        cart.reset_address()
        cart.reset_coupons()
        return Response(cart_serializer.data, status=status.HTTP_200_OK)

    def append_cookie(self, response, cart):
        """Append cart guid to cookie in response

        For each new cart, a new guid is generated and appended to the
        cookie. This guid is used to identify the cart in future requests
        for guest users.
        """
        if not self.request.COOKIES.get('guest_unique_id'):
            response.set_cookie(
                'guest_unique_id',
                cart.guest_unique_id,
                max_age=60 * 60 * 24 * 365)
        return response

    def get_cart(self):
        """Get user cart from request. It may be guest or user cart"""
        user, guid = get_user_or_guest(self.request)
        if user or guid:
            return CartManager.get_user_cart(user, guid)
        return None
