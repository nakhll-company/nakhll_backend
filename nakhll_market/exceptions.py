from django.utils.translation import gettext as _
from rest_framework.exceptions import APIException
from rest_framework import status


class UniqueTitleShopException(APIException):
    default_detail = _('محصولی با این نام در حجره شما وجود دارد')
    status_code = status.HTTP_400_BAD_REQUEST
