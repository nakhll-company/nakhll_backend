from django.utils.translation import gettext as _
from rest_framework.exceptions import APIException


class UnPublishedShop(APIException):
    default_detail = _(
        'فروشگاه به دلایلی قابل دسترس نمی باشد.')
    status_code = 400
