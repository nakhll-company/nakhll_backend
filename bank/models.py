from django.db import models
from django.db.models import F, Q, CheckConstraint
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from bank.constants import NAKHLL_ACCOUNT_ID

from bank.managers import (
    AccountManager,
    AccountRequestManager,
    CoinFuelManager,
    CoinMintageManager)


class CoinMintage(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name=_('ضرب کننده سکه'))
    value = models.PositiveIntegerField(verbose_name=_('مقدار'))
    description = models.TextField(verbose_name=_('توضیحات'))
    date_created = models.DateTimeField(
        auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    objects = CoinMintageManager()

    class Meta:
        verbose_name = _('ضرب سکه')
        verbose_name_plural = _('ضرب های سکه')

    def __str__(self):
        return f'{self.user} - {self.value} - {self.description} - {self.date_created}'


class CoinFuel(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name='سوزاننده سکه')
    value = models.PositiveIntegerField(verbose_name='مقدار')
    description = models.TextField(verbose_name='توضیحات')
    date_created = models.DateTimeField(
        auto_now_add=True, verbose_name='تاریخ ایجاد')
    objects = CoinFuelManager()

    class Meta:
        verbose_name = _("Fuel")
        verbose_name_plural = _("Fuels")

    def __str__(self):
        return f'{self.user} - {self.value} - {self.description} - {self.date_created}'


class Account(models.Model):
    user = models.ForeignKey(
        User,
        unique=True,
        null=True,
        on_delete=models.PROTECT)
    balance = models.PositiveIntegerField(default=0)
    blocked_balance = models.PositiveIntegerField(default=0)
    cashable_amount = models.PositiveIntegerField(default=0)
    blocked_cashable_amount = models.PositiveIntegerField(default=0)
    date_created = models.DateTimeField(auto_now_add=True)
    objects = AccountManager()

    class Meta:
        verbose_name = _("Account")
        verbose_name_plural = _("Accounts")
        constraints = [
            CheckConstraint(
                check=Q(~Q(pk=NAKHLL_ACCOUNT_ID) & ~Q(user=None)) |
                Q(pk=NAKHLL_ACCOUNT_ID, user=None),
                name='only_nakhll_account_can_have_null_user'),
            CheckConstraint(
                check=Q(balance__gte=F('blocked_balance')),
                name='balance_is_more_than_or_equal_to_blocked_balance'),
            CheckConstraint(
                check=Q(cashable_amount__gte=F('blocked_cashable_amount')),
                name='cashable_amount_is_more_than_or_equal_to_blocked_cashable_amount'),
            CheckConstraint(
                check=Q(balance__gte=F('cashable_amount')),
                name='balance_is_more_than_or_equal_to_cashable_amount'),
            CheckConstraint(
                check=Q(blocked_balance__gte=F('blocked_cashable_amount')),
                name='blocked_balance_is_more_than_or_equal_to_blocked_cashable_amount')]

    def __str__(self):
        return f'{self.user} - balance:{self.balance} - cashable amount:{self.cashable_amount}'

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        '''coin only can be transferred to account'''
        if self.pk is None:
            self.balance = self.cashable_amount = self.blocked_balance = self.blocked_cashable_amount = 0
        return super().save(force_insert, force_update, using, update_fields)

    @property
    def net_balance(self):
        return self.balance - self.blocked_balance

    @property
    def net_cashable_amount(self):
        return self.cashable_amount - self.blocked_cashable_amount

    @classmethod
    def get_nakhll_account(cls):
        return cls.objects.get(pk=NAKHLL_ACCOUNT_ID)

    @classmethod
    def get_nakhll_account_blocked(cls):
        return cls.objects.select_for_update().get(pk=NAKHLL_ACCOUNT_ID)

    def withdraw(self, amount=None):
        amount = amount if amount else self.cashable_amount
        AccountRequest.objects.create(
            from_account=self,
            to_account=Account.objects.nakhll_account,
            value=amount,
            request_type=AccountRequest.RequestType.WITHDRAW,
            description='withdraw',
        )


class AccountTransaction(models.Model):
    request = models.ForeignKey(
        'AccountRequest', on_delete=models.PROTECT)
    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='account_transaction')
    account_opposite = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='account_opposite_transaction')
    value = models.IntegerField()
    cashable = models.BooleanField(default=False)
    description = models.CharField(max_length=1023)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("AccountTransaction")
        verbose_name_plural = _("AccountTransaction")

    def __str__(self):
        return f'{self.account} - {self.transaction_type} - {self.amount} - {self.date_created}'


class AccountRequest(models.Model):
    class RequestType(models.IntegerChoices):
        WITHDRAW = 0, _('درخواست تسویه')
    from_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='from_account_request')
    to_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='to_account_request')
    value = models.PositiveIntegerField()
    request_type = models.IntegerField(choices=RequestType.choices)
    description = models.CharField(max_length=1023)
    date_created = models.DateTimeField(auto_now_add=True)
    date_confirmed = models.DateTimeField(null=True, blank=True)
    date_rejected = models.DateTimeField(null=True, blank=True)
    objects = AccountRequestManager()

    class Meta:
        verbose_name = _("AccountRequest")
        verbose_name_plural = _("AccountRequest")

    def __str__(self):
        return self.name

    def is_withdraw(self):
        '''we can check it by to account, so I create this method to have flexibility in statuses'''
        return self.request_type == self.RequestType.WITHDRAW

    def is_cashable(self):
        '''TODO, WE MUST DEFINE IT'''
        return self.is_withdraw()

    def generate_withdraw_transaction_description(self):
        return f'{self.from_account} - {self.to_account} - {self.value}'

    def generate_deposit_transaction_description(self):
        return f'{self.to_account} - {self.from_account} - {self.value}'
