from functools import cached_property
from django.db import models, transaction
from django.db.models import F
from bank.account_requests import (
    CreateRequest, ConfirmRequest, RejectRequest
)
from bank.constants import NAKHLL_ACCOUNT_ID


class OnlyInsertAndRead:
    '''we also have modifying object from save method
    and we have bulk_update method
    '''

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise Exception('you can\'t update coin')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise Exception('you can\'t delete coin')

    def update(self, *args, **kwargs):
        raise Exception('you can\'t update coin')


class AccountManager(models.Manager):
    @property
    def nakhll_account(self):
        return self.get_queryset().get(pk=NAKHLL_ACCOUNT_ID)

    @property
    def nakhll_account_for_update(self):
        return self.get_queryset().select_for_update().get(pk=NAKHLL_ACCOUNT_ID)


class AccountRequestManager(models.Manager):
    '''#TODO: we must prevent update of account request after confirmation and rejection'''

    def create(self, *args, **kwargs):
        with transaction.atomic():
            account_request = self.get_queryset().create(*args, **kwargs)
            CreateRequest(account_request).create()

    def confirm(self, *args, **kwargs):
        '''confirm account request
        validate request
        then confirm it
        '''
        with transaction.atomic():
            account_request = self.get_account_request(*args, **kwargs)
            ConfirmRequest(account_request).confirm()

    def reject(self, *args, **kwargs):
        with transaction.atomic():
            account_request = self.get_account_request(*args, **kwargs)
            RejectRequest(account_request).reject()

    def get_account_request(self, *args, **kwargs):
        '''
        TODO: if we know that account_request is not modifiable, so we can remove select_for_update'''
        return self.get_queryset().select_for_update().get(*args, **kwargs)


class ChangeBalance(OnlyInsertAndRead, models.Manager):
    def create(self, **kwargs):
        from bank.models import Account
        with transaction.atomic():
            self.validate(**kwargs)
            nakhll_account = Account.objects.nakhll_account_for_update
            nakhll_account.balance += self.get_value(**kwargs)
            nakhll_account.save()
            return super().create(**kwargs)

    def get_value(self, **kwargs):
        return kwargs['value']

    def validate(self, **kwargs):
        '''validate request'''


class CoinMintageManager(ChangeBalance):
    '''Coin Mintage Logic
    on create it will add value to balance of nakhll account
    delete and update are not allowed
    '''


class CoinFuelManager(ChangeBalance):
    '''Coin Fuel Logic
    on create it will subtract value from balance of nakhll account
    but we must decide on coin fuel we subtract from nakhll balance or net balance
    if we let user to subtract from balance some of account request will be blocked
    on the other way if we let user to subtract from net balance, user can't fuel coins that are blocked
    delete and update are not allowed
    '''

    def get_value(self, **kwargs):
        return -kwargs['value']

    def validate(self, **kwargs):
        from bank.models import Account
        if kwargs['value'] > Account.objects.nakhll_account_for_update.net_balance:
            raise Exception('not enough cashable amount')
