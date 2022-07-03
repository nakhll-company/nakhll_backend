import uuid
from datetime import datetime, timedelta
from django.db import models
from django.utils import timezone
from .validators import mobile_number_validator

# Create your models here.

def fivemin_from_now():
    return timezone.now() + timedelta(minutes=5)

def generate_uuid_code():
    return uuid.uuid4().hex


class AuthRequestManager(models.Manager):
    def get_by_secret(self, secret):
        try:
            return self.get(auth_secret=secret, request_status=AuthRequest.RequestStatuses.PENDING)
        except AuthRequest.DoesNotExist:
            return None


class AuthRequest(models.Model):
    class Meta:
        verbose_name = 'درخواست احراز هویت'
        verbose_name_plural = 'درخواست احراز هویت'

    class MobileStatuses(models.TextChoices):
        NOT_REGISTERED = 'not_reg', 'شماره موبایل ثبت نشده است'
        LOGIN_WITH_CODE = 'login_code', 'ورود با کد'
        LOGIN_WITH_PASSWORD = 'login_pass', 'ورود با کلمه عبور'
    class RequestStatuses(models.TextChoices):
        PENDING = 'pending', 'در انتظار'
        COMPLETED = 'completed', 'پایان یافته'
    class RequestTypes(models.TextChoices):
        LOGIN_REGISTER = 'signin/up', 'ورود/ثبت‌نام'
        FORGOT_PASSWORD = 'forgotpass', 'فراموشی کلمه عبور'

    mobile = models.CharField(max_length=11, validators=[mobile_number_validator])
    referral_code = models.CharField(max_length=6, null=True)
    sms_code = models.CharField(max_length=6, null=True, blank=True)
    auth_key = models.CharField(max_length=32, default=generate_uuid_code)
    auth_secret = models.CharField(max_length=32, null=True, blank=True)
    expire_datetime = models.DateTimeField(default=fivemin_from_now)
    mobile_status = models.CharField(max_length=10, choices=MobileStatuses.choices)
    request_status = models.CharField(max_length=10, choices=RequestStatuses.choices, default=RequestStatuses.PENDING)
    request_type = models.CharField(max_length=10, choices=RequestTypes.choices, default=RequestTypes.LOGIN_REGISTER)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = AuthRequestManager()

    def __str__(self):
        return self.mobile + ' - ' + self.created_at

    def is_expired(self):
        return timezone.now() > self.expire_datetime

    def close_request(self):
        self.request_status = self.RequestStatuses.COMPLETED
        self.save()