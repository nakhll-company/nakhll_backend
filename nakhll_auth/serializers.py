from django.contrib.auth import authenticate
from django.contrib.auth.models import User, update_last_login
from django.utils import timezone
from rest_framework import serializers, status, validators
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken
from .models import AuthRequest


class BeginAuthSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthRequest
        fields = ('mobile', 'auth_key', 'mobile_status', 'referral_code')
        read_only_fields = ('auth_key', 'mobile_status', )
    
    def to_representation(self, obj):
        ret = super(BeginAuthSerializer, self).to_representation(obj)
        ret.pop('mobile')
        ret.pop('referral_code')
        return ret

class CompleteAuthSerializer(serializers.ModelSerializer):
    user_key = serializers.CharField(max_length=32)
    class Meta:
        model = AuthRequest
        fields = ('auth_secret', 'auth_key', 'user_key')
        write_only_fields = ('auth_secret', )

    def validate(self, data):
        auth_key = data.get('auth_key')
        user_key = data.get('user_key')
        self.instance = self._get_auth_request(auth_key)
        if not self.auth_is_valid(self.instance, user_key):
            raise serializers.ValidationError({'password': 'اطلاعات برای احراز هویت معتبر نیست'}, code=status.HTTP_401_UNAUTHORIZED)
        return data

    def auth_is_valid(self, auth_request, user_key):
        if  auth_request.mobile_status == AuthRequest.MobileStatuses.LOGIN_WITH_PASSWORD\
                and auth_request.request_type != AuthRequest.RequestTypes.FORGOT_PASSWORD:
            return self.__validate_password(auth_request, user_key)
        return self.__validate_code(auth_request, user_key)
     
    def _get_auth_request(self, auth_key):
        try:
            return AuthRequest.objects.get(auth_key=auth_key, request_status=AuthRequest.RequestStatuses.PENDING)
        except AuthRequest.DoesNotExist:
            raise serializers.ValidationError('درخواستی برای احراز هویت وجود ندارد', code=status.HTTP_400_BAD_REQUEST)

    def __validate_password(self, auth_request, user_key):
        return bool(authenticate(username=auth_request.mobile, password=user_key))
    
    def __validate_code(self, auth_request, user_key):
        if timezone.now() > auth_request.expire_datetime:
            raise serializers.ValidationError('کد منقضی شده است', code=status.HTTP_401_UNAUTHORIZED)
        return bool(user_key == auth_request.sms_code)

    def to_representation(self, obj):
        ret = super(CompleteAuthSerializer, self).to_representation(obj)
        ret.pop('user_key')
        ret.pop('auth_key')
        return ret

class PasswordSerializer(serializers.Serializer):
    auth_secret = serializers.CharField(max_length=32)
    password = serializers.CharField(max_length=128, write_only=True)

    def __init__(self, instance=None, data=..., **kwargs):
        self.request_type = kwargs.pop('request_type')
        super().__init__(instance=instance, data=data, **kwargs)

    def save(self):
        password = self.validated_data['password']
        self.user.set_password(password)
        self.user.save()
        self.auth.close_request()
        return self.auth

    def validate_auth_secret(self, value):
        self.auth = AuthRequest.objects.get_by_secret(value)
        if not self.auth:
            raise serializers.ValidationError('هیچ درخواست احراز هویتی برای درخواست شما یافت نشد. لطفا مجددا تلاش کنید')
        if self.auth.is_expired():
            raise serializers.ValidationError('درخواست احراز هویت منقضی شده است', code=status.HTTP_403_FORBIDDEN)
        self.user = self._get_user(self.auth)
        return value

    def _get_user(self, auth):
        try:
            return User.objects.get(username=auth.mobile)
        except User.DoesNotExist:
            raise serializers.ValidationError('برای این درخواست هیچ کاربری پیدا نشد', code=status.HTTP_400_BAD_REQUEST)

    def to_representation(self, obj):
        ret = super(GetTokenSerializer, self).to_representation(obj)
        ret.pop('auth_secret')
        return ret 

class GetTokenSerializer(serializers.Serializer):
    auth_secret = serializers.CharField(max_length=32)
    
    def validate(self, data):
        self.auth = self._get_auth_request(data.get('auth_secret'))
        self._validate_auth_request()
        self.user = self._get_user(self.auth)
        
        refresh = self.get_token(self.user)
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)

        if api_settings.UPDATE_LAST_LOGIN:
            update_last_login(None, self.user)
        self.auth.close_request()
        return data

    def get_token(self, user):
        return RefreshToken.for_user(user)

    def _get_user(self, auth):
        try:
            return User.objects.get(username=auth.mobile)
        except User.DoesNotExist:
            raise serializers.ValidationError('برای این درخواست هیچ کاربری پیدا نشد', code=status.HTTP_400_BAD_REQUEST)

    def _get_auth_request(self, auth_secret):
        try:
            return AuthRequest.objects.get(auth_secret=auth_secret, request_status=AuthRequest.RequestStatuses.PENDING)
        except:
            raise serializers.ValidationError('درخواستی برای احراز هویت وجود ندارد', code=status.HTTP_400_BAD_REQUEST)
        
    def _validate_auth_request(self):
        if not self.auth:
            raise serializers.ValidationError('هیچ درخواست احراز هویتی برای درخواست شما یافت نشد. لطفا مجددا تلاش کنید')
        if self.auth.is_expired():
            raise serializers.ValidationError('درخواست احراز هویت منقضی شده است', code=status.HTTP_403_FORBIDDEN)
