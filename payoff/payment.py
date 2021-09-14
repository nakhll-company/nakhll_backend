import os
from abc import ABC, abstractmethod
from django.shortcuts import redirect
from django.conf import settings
from django.apps import apps
from django.utils.translation import ugettext as _
from rest_framework.response import Response
from rest_framework.validators import ValidationError
from payoff.models import Transaction, TransactionResult
from payoff.exceptions import NoTransactionException
from zeep import Client


class PaymentMethod(ABC):
    def __init__(self, *args, **kwargs):
        self.transaction = None

    @abstractmethod
    def initiate_payment(self, data):
        ''' Generate ipg url and redirect user to that url '''

    @abstractmethod
    def callback(self, data):
        ''' Handle returned data from IPG 
        
            Validate IPG response and update transaction result, connect data
            to transaction object
        '''

class Pec(PaymentMethod):

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        # TODO: These errors should be handled better with better messages
        pec_pin = os.environ.get('PEC_PIN')
        callback_url = format(os.environ.get('CALLBACKURL'))
        if not pec_pin:
            raise ValidationError(_('در حال حاضر امکان اتصال به درگاه بانکی وجود ندارد'))
        if not callback_url:
            raise ValidationError(_('در حال حاضر امکان اتصال به درگاه بانکی وجود ندارد'))
        self.pec_pin = pec_pin
        self.callback_url = callback_url
        self.sale_service = self.__get_sale_serivce()
        self.sale_request_data = self.__get_client_sale_request_data()
        self.confirm_service = self.__get_confirm_service()

    def __get_sale_serivce(self):
        return Client(
            'https://pec.shaparak.ir/NewIPGServices/Sale/SaleService.asmx?wsdl')

    def __get_confirm_service(self):
        return Client(
            'https://pec.shaparak.ir/NewIPGServices/Confirm/ConfirmService.asmx?wsdl')

    def __get_client_sale_request_data(self):
        return self.sale_service.get_type('ns0:ClientSaleRequestData')
        

    def initiate_payment(self, data):
        ''' Get invoice, exchange with token and redirect user to payment page '''
        print(f'IN: payoff > payment.py > Pec class > _initate_payment')
        self.transaction = self._create_transaction(data)
        token_object = self._get_token_object()
        self._save_token_object(token_object)
        if not self.is_token_object_valid(token_object):
            raise ValidationError(f'{token_object.Status} {token_object.Message}')
        print(f'\t token: {token_object.Token}')
        print('\n>>>>>>>>>>>>>>>>Redirecting<<<<<<<<<<<<<<<<<<<\n')
        url = f'https://pec.shaparak.ir/NewIPG/?token={token_object.Token}'
        return redirect(url)

    def _get_token_object(self):
        ''' Get sale service and send invocie data to it, return token if 
            invoice data is valid 
        '''
        print(f'IN: payoff > payment.py > Pec class > _get_token')
        print(f'\t transaction: {self.transaction}')
        print(f'\t transaction: {self.transaction.__dict__}')

        token_request_object = self._generate_token_request_object()
        print(f'\t token_request_object: {token_request_object}')
        print(f'\t token request object type: {type(token_request_object)}')

        token_response_object = self._get_token_response_object(
            token_request_object)
        print(f'\t token_response_object: {token_response_object}')
        print(f'\t token response object type: {type(token_response_object)}')
        
        return token_response_object

        
    def _generate_token_request_object(self):
        return self.sale_request_data(
            LoginAccount=self.pec_pin,
            Amount=self.transaction.amount,
            OrderId=self.transaction.order_number,
            CallBackUrl=self.callback_url,
            AdditionalData=self.transaction.description,
            Originator=self.transaction.mobile)

    def _get_token_response_object(self, token_request):
        ''' Send token request to IPG and return response object '''
        return self.sale_service.service.SalePaymentRequest(token_request)

    def is_token_object_valid(self, token_object):
        ''' Check if token is valid '''
        SUCCESS_STATUS_NUMBER = 0
        SUCCESS_TOKEN_MIN_VALUE = 0
        return False if token_object.Status != SUCCESS_STATUS_NUMBER\
            or token_object.Token <= SUCCESS_TOKEN_MIN_VALUE else True

    def _save_token_object(self, token_object):
        ''' Store result of token request from IPG to DB'''
        print(f'\t _save_sale_payment_result:')
        print(f'\t token object is: {token_object}')
        print(f'\t token object type is: {type(token_object)}')
        print(f'\t token object attributes are: {dir(token_object)}')
        self.transaction.token_request_status =token_object.Status
        self.transaction.token_request_message = token_object.Message
        self.transaction.token = token_object.Token
        self.transaction.save()


    def callback(self, data):
        ''' Get data from Pec gateway and render it'''
        parsed_data = self._parse_callback_data(data)
        print(f'Parsed data:\t {parsed_data}')
        transaction_result = self._create_transaction_result(parsed_data)
        transaction_result = self._link_to_transaction(transaction_result)
        if self._is_tarnsaction_result_succeded(transaction_result)\
            and self._validate_transaction_result(transaction_result):
            return self._complete_payment(transaction_result)
        return self._revert_transaction(transaction_result)

    def _parse_callback_data(self, data):
        ''' Parse data from Pec gateway '''
        print(f'IN: payoff > payment.py > Pec class > _parse_callback_data')
        print(f'\t data: {data}')
        print(f'\t type: {type(data)}')
        return {
            'token': data.get('Token', 0),
            'order_id': data.get('OrderId', 0),
            'terminal_no': data.get('TerminalNo', 0),
            'rrn': data.get('RRN', 0),
            'status': data.get('status', 200),
            'hash_card_number': data.get('HashCardNumber', ''),
            'amount': self._parse_amount(data.get('Amount', 0)),
            'discounted_amount': self._parse_amount(data.get('SwAmount', 0)),
        }

    def _parse_amount(self, amount):
        ''' Parse amount from Pec gateway '''
        return int(amount.replace(',',''))

    def _create_transaction(self, data):
        transaction = Transaction.objects.create(**data)
        print(f'\t Transaction created: {transaction}')
        return transaction

    def _create_transaction_result(self, data):
        transaction_result = TransactionResult.objects.create(**data)
        print(f'Transaction result created: {transaction_result}')
        return transaction_result

    def _link_to_transaction(self, transaction_result):
        try:
            transaction = Transaction.objects.get(
                order_number=transaction_result.order_id)
        except:
            raise NoTransactionException(f'No transaction found for order_id:\
                {transaction_result.order_id}')
        transaction_result.transaction = transaction
        transaction_result.save()
        return transaction_result

    def _is_tarnsaction_result_succeded(self, transaction_result):
        ''' Send request to IGP validation url and validate transaction '''
        SUCCESS_STATUS_CODE = 0
        SUCCESS_RRN_MIN_VALUE = 0
        if transaction_result.status_code == SUCCESS_STATUS_CODE\
            and transaction_result.rrn > SUCCESS_RRN_MIN_VALUE:
            return True
        return False

    def _validate_payment(self, transaction_result):
        #TODO: Need cleaning
        ''' Validate payment '''
        token = transaction_result.transaction.token
        pec_pin = self.pec_pin
        request_data = self.confirm_service(Token=token, LoginAccount=pec_pin)
        result = self.confirm_service.service.ConfirmPaymentRequest(request_data)
        token = result.get('Token', 0)
        if token <= 0 or result.get('Status', 0) != 0:
            # TODO: create alert for support to handle this
            return False
        return True



    def _complete_payment(self, transaction_result):
        ''' Send transaction_result to referrer model to finish purchase process'''
        app_label = transaction_result.transaction.referrer_app
        model_name = transaction_result.transaction.referrer_model
        referrer_model = apps.get_model(app_label, model_name) 
        referrer_model.complete_payment(transaction_result.transaction)

    def _revert_transaction(self, transaction_result):
        ''' Send transaction_result to referrer model to finish purchase process'''
        app_label = transaction_result.transaction.referrer_app
        model_name = transaction_result.transaction.referrer_model
        referrer_model = apps.get_model(app_label, model_name) 
        referrer_model.revert_payment(transaction_result.transaction)





class ZarinPal(PaymentMethod):
    ''' Zarinpal ipg implementation '''



class Payment:
    @staticmethod
    def initiate_payment(data):
        print(f'\n\nIN: payoff > payment.py > Peyment > _initate_payment')
        print(f'\t data: {data}')
        ipg_type = data.get('ipg')
        ipg_class = Payment._get_ipg_class(ipg_type)
        print(f'\tIPG class: {ipg_class}')
        ipg = ipg_class()
        return ipg.initiate_payment(data)

    @staticmethod
    def payment_callback(data, ipg_type):
        ipg_class = Payment._get_ipg_class(ipg_type)
        ipg = ipg_class()
        return ipg.callback(data)

    @staticmethod
    def _get_ipg_class(ipg_type):
        if ipg_type == Transaction.IPGTypes.PEC:
            return Pec
        if ipg_type == Transaction.IPGTypes.ZARINPAL:
            return ZarinPal


