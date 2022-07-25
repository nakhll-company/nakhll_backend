from functools import cached_property
from warnings import catch_warnings
from django.db.models import F
from django.utils import timezone


class BaseAccountRequest:

    def __init__(self, account_request) -> None:
        from bank.models import Account
        self.account_request = account_request
        self.from_account = Account.objects.select_for_update().filter(
            pk=self.account_request.from_account_id)
        self.to_account = Account.objects.select_for_update().filter(
            pk=self.account_request.to_account_id)

    def validate(self):
        ''' validate request:
        1. from account balance is greater than or equal to request value
        (now we create this fields as positive integer fields, so django will create
        a constraint for them in DB, but we can send user friendly error messages by
        checking them in python too.)
        2. for withdraw, cashable amount is greater than or equal to request value
        it get one account request and confirm it'''
        if self.account_request.is_withdraw():
            if self.from_account.first().net_cashable_amount < self.account_request.value:
                raise Exception('not enough cashable amount')
        if self.from_account.first(
        ).net_balance < self.account_request.value:
            raise Exception('not enough balance')

    def lock_account_request(self):
        '''when a request is confirmed, we lock it so it can't be changed anymore
        '''


class CreateRequest(BaseAccountRequest):

    def create(self):
        self.validate()
        self.block_account_balance_and_cashable_amount()

    def block_account_balance_and_cashable_amount(self):
        self.from_account.update(
            blocked_balance=F('blocked_balance') +
            self.account_request.value)
        if self.account_request.is_withdraw():
            self.from_account.update(
                blocked_cashable_amount=F('blocked_cashable_amount') +
                self.account_request.value)


class ConfirmRequest(BaseAccountRequest):

    def confirm(self):
        self.validate()
        self.__confirm()

    def __confirm(self):
        '''this will confirm request
        and update accounts balance and cashable amount
        and generate transactions
        '''
        self.__update_accounts_balance_and_cashable_amount()
        self.__generate_transactions()
        self.__update_account_request_status()
        self.lock_account_request()

    def __update_accounts_balance_and_cashable_amount(self):
        '''update accounts balance and cashable amount
        '''
        self.__update_balance()
        self.__update_cashable_amount()

    def __update_balance(self):
        self.from_account.update(
            blocked_balance=F('blocked_balance') - self.account_request.value,
            balance=F('balance') - self.account_request.value)
        self.to_account.update(
            balance=F('balance') + self.account_request.value)

    def __update_cashable_amount(self):
        if self.account_request.is_withdraw():
            self.from_account.update(
                cashable_amount=F('cashable_amount') -
                self.account_request.value,
                blocked_cashable_amount=F('blocked_cashable_amount') -
                self.account_request.value)

    def __generate_transactions(self):
        self.__generate_withdraw_transaction()
        self.__generate_deposit_transaction()

    def __generate_withdraw_transaction(self):
        from bank.models import AccountTransaction
        AccountTransaction.objects.create(
            request=self.account_request,
            account=self.from_account,
            account_opposite=self.to_account,
            value=self.account_request.value * -1,
            cashable=self.account_request.is_cashable(),
            description=self.account_request.generate_withdraw_transaction_description(),
        )

    def __generate_deposit_transaction(self):
        from bank.models import AccountTransaction
        AccountTransaction.objects.create(
            request=self.account_request,
            account=self.to_account,
            account_opposite=self.from_account,
            value=self.account_request.value,
            cashable=self.account_request.is_cashable(),
            description=self.account_request.generate_deposit_transaction_description(),
        )

    def __update_account_request_status(self):
        self.account_request.update(date_confirmed=timezone.now())


class RejectRequest(BaseAccountRequest):

    def reject(self):
        self.__reject()

    def __reject(self):
        self.__update_accounts_balance_and_cashable_amount()
        self.__update_account_request_status()
        self.lock_account_request()

    def __update_accounts_balance_and_cashable_amount(self):
        self.__update_blocked_balance()
        self.__update_blocked_cashable_amount()

    def __update_blocked_balance(self):
        self.from_account.update(
            blocked_balance=F('blocked_balance') - self.account_request.value)

    def __update_blocked_cashable_amount(self):
        if self.account_request.is_withdraw():
            self.from_account.update(
                blocked_cashable_amount=F('blocked_cashable_amount') -
                self.account_request.value)

    def __update_account_request_status(self):
        self.account_request.update(date_rejected=timezone.now())
