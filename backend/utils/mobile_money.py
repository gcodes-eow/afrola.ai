# backend/utils/mobile_money.py

import os
import hashlib
import base64
import requests
import json
import uuid
import logging
from datetime import datetime
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


class AirtelMoney:
    """Airtel Mobile Money API Integration"""

    def __init__(self):
        self.api_url = settings.AIRTEL_MONEY_API_URL
        self.client_id = settings.AIRTEL_MONEY_CLIENT_ID
        self.client_secret = settings.AIRTEL_MONEY_CLIENT_SECRET
        self.api_key = settings.AIRTEL_MONEY_API_KEY
        self.pin = settings.AIRTEL_MONEY_PIN
        self.country = settings.AIRTEL_MONEY_COUNTRY
        self.currency = settings.AIRTEL_MONEY_CURRENCY
        self.timeout = settings.MOBILE_MONEY_TIMEOUT
        self.enabled = settings.AIRTEL_MONEY_ENABLED

    def get_access_token(self):
        """Get OAuth access token from Airtel"""
        cache_key = 'airtel_access_token'
        token = cache.get(cache_key)

        if token:
            return token

        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_string.encode('ascii')
        auth_base64 = base64.b64encode(auth_bytes).decode('ascii')

        headers = {
            'Authorization': f'Basic {auth_base64}',
            'Content-Type': 'application/json',
            'X-Country': self.country,
            'X-Currency': self.currency
        }

        try:
            response = requests.post(
                f"{self.api_url}/auth/oauth2/token",
                headers=headers,
                json={"grant_type": "client_credentials"},
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                token = data.get('access_token')
                expires_in = data.get('expires_in', 3600)
                cache.set(cache_key, token, expires_in - 60)
                return token

            logger.error(f"Airtel token error: {response.text}")
            return None
        except requests.RequestException as e:
            logger.error(f"Airtel token request failed: {e}")
            return None

    def initiate_payment(self, phone_number, amount, reference):
        """Initiate a payment request to Airtel Money"""
        if not self.enabled:
            return {'success': False, 'message': 'Airtel Money not enabled'}

        token = self.get_access_token()
        if not token:
            return {'success': False, 'message': 'Could not authenticate with Airtel'}

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'X-Country': self.country,
            'X-Currency': self.currency,
            'api-key': self.api_key
        }

        payload = {
            "reference": reference,
            "subscriber": {
                "country": self.country,
                "currency": self.currency,
                "msisdn": phone_number
            },
            "transaction": {
                "amount": str(amount),
                "country": self.country,
                "currency": self.currency,
                "id": reference
            }
        }

        try:
            response = requests.post(
                f"{self.api_url}/standard/v1/payments",
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            return {'success': True, 'reference': reference, 'data': response.json()}
        except requests.RequestException as e:
            logger.error(f"Airtel payment failed: {e}")
            return {'success': False, 'message': str(e)}

    def check_payment_status(self, reference):
        """Check the status of a payment"""
        token = self.get_access_token()
        if not token:
            return {'status': 'UNKNOWN'}

        headers = {
            'Authorization': f'Bearer {token}',
            'X-Country': self.country
        }

        try:
            response = requests.get(
                f"{self.api_url}/standard/v1/payments/{reference}",
                headers=headers,
                timeout=self.timeout
            )
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Airtel status check failed: {e}")
            return {'status': 'ERROR'}


class MTNMoney:
    """MTN Mobile Money API Integration"""

    def __init__(self):
        self.api_url = settings.MTN_MONEY_API_URL
        self.subscription_key = settings.MTN_MONEY_SUBSCRIPTION_KEY
        self.api_user = settings.MTN_MONEY_API_USER
        self.api_key = settings.MTN_MONEY_API_KEY
        self.pin = settings.MTN_MONEY_PIN
        self.country = settings.MTN_MONEY_COUNTRY
        self.currency = settings.MTN_MONEY_CURRENCY
        self.timeout = settings.MOBILE_MONEY_TIMEOUT
        self.callback_url = settings.MTN_MONEY_CALLBACK_URL
        self.environment = settings.MOBILE_MONEY_ENVIRONMENT
        self.enabled = settings.MTN_MONEY_ENABLED

    def get_access_token(self):
        """Get OAuth access token from MTN"""
        cache_key = 'mtn_access_token'
        token = cache.get(cache_key)

        if token:
            return token

        auth_string = f"{self.api_user}:{self.api_key}"
        auth_bytes = auth_string.encode('ascii')
        auth_base64 = base64.b64encode(auth_bytes).decode('ascii')

        headers = {
            'Authorization': f'Basic {auth_base64}',
            'Ocp-Apim-Subscription-Key': self.subscription_key
        }

        try:
            response = requests.post(
                f"{self.api_url}/token",
                headers=headers,
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                token = data.get('access_token')
                expires_in = data.get('expires_in', 3600)
                cache.set(cache_key, token, expires_in - 60)
                return token

            logger.error(f"MTN token error: {response.text}")
            return None
        except requests.RequestException as e:
            logger.error(f"MTN token request failed: {e}")
            return None

    def initiate_payment(self, phone_number, amount, reference):
        """Initiate a payment request to MTN Money"""
        if not self.enabled:
            return {'success': False, 'message': 'MTN Money not enabled'}

        token = self.get_access_token()
        if not token:
            return {'success': False, 'message': 'Could not authenticate with MTN'}

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Ocp-Apim-Subscription-Key': self.subscription_key,
            'X-Reference-Id': reference,
            'X-Target-Environment': self.environment
        }

        payload = {
            "amount": str(amount),
            "currency": self.currency,
            "externalId": reference,
            "payer": {
                "partyIdType": "MSISDN",
                "partyId": phone_number
            },
            "payerMessage": settings.MOBILE_MONEY_DESCRIPTION,
            "payeeNote": f"Afrola subscription - {reference[:8]}"
        }

        try:
            response = requests.post(
                f"{self.api_url}/requesttopay",
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            if response.status_code in [200, 201, 202]:
                return {'success': True, 'reference': reference, 'data': response.json() if response.text else {}}
            return {'success': False, 'message': response.text}
        except requests.RequestException as e:
            logger.error(f"MTN payment failed: {e}")
            return {'success': False, 'message': str(e)}

    def check_payment_status(self, reference):
        """Check the status of a payment"""
        token = self.get_access_token()
        if not token:
            return {'status': 'UNKNOWN'}

        headers = {
            'Authorization': f'Bearer {token}',
            'Ocp-Apim-Subscription-Key': self.subscription_key,
            'X-Target-Environment': self.environment
        }

        try:
            response = requests.get(
                f"{self.api_url}/requesttopay/{reference}",
                headers=headers,
                timeout=self.timeout
            )
            return response.json()
        except requests.RequestException as e:
            logger.error(f"MTN status check failed: {e}")
            return {'status': 'ERROR'}


class MobileMoneyProcessor:
    """Unified interface for both Airtel and MTN"""

    def __init__(self, provider):
        if provider.lower() == 'airtel':
            self.client = AirtelMoney()
        elif provider.lower() == 'mtn':
            self.client = MTNMoney()
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        self.provider = provider

    def process_payment(self, phone_number, amount, reference):
        """Process payment through selected provider"""
        return self.client.initiate_payment(phone_number, amount, reference)

    def get_status(self, reference):
        """Get payment status"""
        return self.client.check_payment_status(reference)

    def validate_phone_number(self, phone_number, provider):
        """Validate phone number format for specific provider"""
        if provider == 'airtel':
            return phone_number.startswith('2567') and len(phone_number) == 12
        elif provider == 'mtn':
            return phone_number.startswith('25678') and len(phone_number) == 12
        return False


# Helper functions
def get_payment_providers():
    """Get list of enabled payment providers"""
    providers = []
    if settings.AIRTEL_MONEY_ENABLED:
        providers.append('airtel')
    if settings.MTN_MONEY_ENABLED:
        providers.append('mtn')
    if settings.STRIPE_PUBLIC_KEY:
        providers.append('stripe')
    return providers


def format_phone_number(phone_number):
    """Format phone number to international format"""
    cleaned = ''.join(filter(str.isdigit, phone_number))

    if cleaned.startswith('0'):
        cleaned = '256' + cleaned[1:]
    if cleaned.startswith('256'):
        return cleaned
    return '256' + cleaned


def get_phone_provider(phone_number):
    """Determine mobile money provider from phone number"""
    formatted = format_phone_number(phone_number)

    if formatted.startswith('2567'):
        mtn_prefixes = ['25678', '25675']
        if any(formatted.startswith(prefix) for prefix in mtn_prefixes):
            return 'mtn'
        return 'airtel'
    elif formatted.startswith('25678'):
        return 'mtn'
    return None


def validate_mobile_money_payment(amount):
    """Validate payment amount for mobile money"""
    min_amount = settings.MINIMUM_PAYMENT_AMOUNT
    max_amount = settings.MAXIMUM_PAYMENT_AMOUNT

    if amount < min_amount:
        return False, f"Minimum payment amount is {min_amount} UGX"
    if amount > max_amount:
        return False, f"Maximum payment amount is {max_amount} UGX"
    return True, "Valid amount"


def generate_reference():
    """Generate unique payment reference"""
    return str(uuid.uuid4())[:12]
