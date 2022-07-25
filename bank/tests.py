from django.test import TestCase

# Create your tests here.
from django.contrib.auth.models import User
from bank.models import Account, AccountRequest, CoinFuel, CoinMintage
from bank.constants import NAKHLL_ACCOUNT_ID


class AccountTestCase(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.get(username='dummy')
        self.nakhll_account = Account.objects.nakhll_account

    def test_create_account(self):
        account = Account.objects.create(user=self.user)
        self.assertEqual(account.user, self.user)
        self.assertEqual(account.balance, 0)
        self.assertEqual(account.blocked_balance, 0)
        self.assertEqual(account.cashable_amount, 0)
        self.assertEqual(account.blocked_cashable_amount, 0)
        self.assertNotEqual(account.id, NAKHLL_ACCOUNT_ID)

    def test_nakhll_account_user_is_none(self):
        self.assertIsNone(self.nakhll_account.user)

    def test_can_not_generate_nullable_user(self):
        with self.assertRaises(Exception):
            Account.objects.create()

    def test_can_not_generate_account_with_nakhll_id(self):
        with self.assertRaises(Exception):
            Account.objects.create(id=NAKHLL_ACCOUNT_ID, user=self.user)


class CoinMintageTestCase(TestCase):
    def test_mintage_coin(self):
        user = User.objects.get(username='dummy')
        self.assertEqual(Account.objects.nakhll_account.balance, 0)
        CoinMintage.objects.create(user=user, value=1)
        self.assertEqual(Account.objects.nakhll_account.balance, 1)


class CoinFuelTestCase(TestCase):
    def test_fuel_coin(self):
        user = User.objects.get(username='dummy')
        nakhll_account = Account.objects.nakhll_account
        nakhll_account.balance = 1
        nakhll_account.save()
        self.assertEqual(nakhll_account.balance, 1)
        CoinFuel.objects.create(user=user, value=1)
        self.assertEqual(Account.objects.nakhll_account.balance, 0)


class WithdrawTestCase(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.get(username='dummy')
        self.nakhll_account = Account.objects.nakhll_account
        self.account = Account.objects.create(user=self.user)

    def test_withdraw(self):
        self.account.balance = 100
        self.account.cashable_amount = 50
        self.account.save()
        self.account.withdraw(50)
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, 100)
        self.assertEqual(self.account.blocked_balance, 50)
        self.assertEqual(self.account.cashable_amount, 50)
        self.assertEqual(self.account.blocked_cashable_amount, 50)
        self.assertEqual(self.nakhll_account.balance, 0)

    def test_can_not_withdraw_more_than_net_cashable_amount(self):
        self.account.balance = 100
        self.account.blocked_balance = 60
        self.account.cashable_amount = 50
        self.account.blocked_cashable_amount = 40
        self.account.save()
        self.account.refresh_from_db()
        with self.assertRaises(Exception):
            self.account.withdraw(11)

    def test_balance_is_more_than_or_equal_to_blocked_balance(self):
        self.account.balance = 5
        self.account.blocked_balance = 10
        with self.assertRaises(Exception):
            self.save()

    def test_balance_is_more_than_or_equal_to_cashable_amount(self):
        self.account.balance = 10
        self.account.cashable_amount = 20
        with self.assertRaises(Exception):
            self.account.save()

    def test_blocked_balance_is_more_than_or_equal_to_blocked_cashable_amount(
            self):
        self.account.balance = 100
        self.account.cashable_amount = 50
        self.account.blocked_balance = 40
        self.account.blocked_cashable_amount = 41
        with self.assertRaises(Exception):
            self.account.save()


class ConfirmTestCase(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.get(username='dummy')
        self.nakhll_account = Account.objects.nakhll_account
        self.account = Account.objects.create(user=self.user)
        self.account.balance = 100
        self.account.cashable_amount = 50
        self.account.save()
        self.account.refresh_from_db()

    def test_confirm_withdraw_request(self):
        self.account.withdraw(50)
        AccountRequest.objects.confirm(from_account=self.account.id)
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, 50)
        self.assertEqual(self.account.blocked_balance, 0)
        self.assertEqual(self.account.cashable_amount, 0)
        self.assertEqual(self.account.blocked_cashable_amount, 0)


class RejectTestCase(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.get(username='dummy')
        self.nakhll_account = Account.objects.nakhll_account
        self.account = Account.objects.create(user=self.user)
        self.account.balance = 100
        self.account.cashable_amount = 50
        self.account.save()
        self.account.refresh_from_db()
        self.account.withdraw(50)

    def test_reject_withdraw_request(self):
        AccountRequest.objects.get(from_account=self.account.id).reject()
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, 100)
        self.assertEqual(self.account.blocked_balance, 0)
        self.assertEqual(self.account.cashable_amount, 50)
        self.assertEqual(self.account.blocked_cashable_amount, 0)
