"""
Mobile Money utility functions for Airtel and MTN integrations
"""
import os
import hashlib
import base64
import requests
import json
from datetime import datetime
from django.core.cache import cache

class AirtelMoney:
    """Airtel Mobile Money API Integration"""
    
    def __init__(self):
        self.api_url = os.getenv('AIRTEL_MONEY_API_URL')
        self.client_id = os.getenv('AIRTEL_MONEY_CLIENT_ID')
        self.client_secret = os.getenv('AIRTEL_MONEY_CLIENT_SECRET')
        self.api_key = os.getenv('AIRTEL_MONEY_API_KEY')
        self.pin = os.getenv('AIRTEL_MONEY_PIN')
        self.country = os.getenv('AIRTEL_MONEY_COUNTRY', 'UG')
        self.currency = os.getenv('AIRTEL_MONEY_CURRENCY', 'UGX')
        self.timeout = int(os.getenv('MOBILE_MONEY_TIMEOUT', 30))
        
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
            cache.set(cache_key, token, expires_in - 60)  # Cache for slightly less than expiry
            return token
        
        raise Exception(f"Airtel token error: {response.text}")
    
    def initiate_payment(self, phone_number, amount, reference):
        """Initiate a payment request to Airtel Money"""
        token = self.get_access_token()
        
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
        
        response = requests.post(
            f"{self.api_url}/standard/v1/payments",
            headers=headers,
            json=payload,
            timeout=self.timeout
        )
        
        return response.json()
    
    def check_payment_status(self, reference):
        """Check the status of a payment"""
        token = self.get_access_token()
        
        headers = {
            'Authorization': f'Bearer {token}',
            'X-Country': self.country
        }
        
        response = requests.get(
            f"{self.api_url}/standard/v1/payments/{reference}",
            headers=headers,
            timeout=self.timeout
        )
        
        return response.json()


class MTNMoney:
    """MTN Mobile Money API Integration"""
    
    def __init__(self):
        self.api_url = os.getenv('MTN_MONEY_API_URL')
        self.subscription_key = os.getenv('MTN_MONEY_SUBSCRIPTION_KEY')
        self.api_user = os.getenv('MTN_MONEY_API_USER')
        self.api_key = os.getenv('MTN_MONEY_API_KEY')
        self.pin = os.getenv('MTN_MONEY_PIN')
        self.country = os.getenv('MTN_MONEY_COUNTRY', 'UG')
        self.currency = os.getenv('MTN_MONEY_CURRENCY', 'UGX')
        self.timeout = int(os.getenv('MOBILE_MONEY_TIMEOUT', 30))
        
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
        
        raise Exception(f"MTN token error: {response.text}")
    
    def initiate_payment(self, phone_number, amount, reference):
        """Initiate a payment request to MTN Money"""
        token = self.get_access_token()
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Ocp-Apim-Subscription-Key': self.subscription_key,
            'X-Target-Environment': os.getenv('MOBILE_MONEY_ENVIRONMENT', 'sandbox')
        }
        
        payload = {
            "amount": str(amount),
            "currency": self.currency,
            "externalId": reference,
            "payer": {
                "partyIdType": "MSISDN",
                "partyId": phone_number
            },
            "payerMessage": "Afrola.ai Payment",
            "payeeNote": "Subscription payment"
        }
        
        response = requests.post(
            f"{self.api_url}/requesttopay",
            headers=headers,
            json=payload,
            timeout=self.timeout
        )
        
        return response.status_code, response.text
    
    def check_payment_status(self, reference):
        """Check the status of a payment"""
        token = self.get_access_token()
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Ocp-Apim-Subscription-Key': self.subscription_key,
            'X-Target-Environment': os.getenv('MOBILE_MONEY_ENVIRONMENT', 'sandbox')
        }
        
        response = requests.get(
            f"{self.api_url}/requesttopay/{reference}",
            headers=headers,
            timeout=self.timeout
        )
        
        return response.json()


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
            # Airtel numbers typically start with 2567
            return phone_number.startswith('2567') and len(phone_number) == 12
        elif provider == 'mtn':
            # MTN numbers typically start with 25678
            return phone_number.startswith('25678') and len(phone_number) == 12
        return False

# Helper functions
def get_payment_providers():
    """Get list of enabled payment providers"""
    providers = []
    if os.getenv('AIRTEL_MONEY_ENABLED') == 'True':
        providers.append('airtel')
    if os.getenv('MTN_MONEY_ENABLED') == 'True':
        providers.append('mtn')
    if os.getenv('STRIPE_PUBLIC_KEY'):
        providers.append('stripe')
    return providers

def format_phone_number(phone_number):
    """Format phone number to international format"""
    # Remove any non-digit characters
    cleaned = ''.join(filter(str.isdigit, phone_number))
    
    # If starts with 0, replace with 256
    if cleaned.startswith('0'):
        cleaned = '256' + cleaned[1:]
    
    # If starts with 256, keep as is
    if cleaned.startswith('256'):
        return cleaned
    
    # Default to Uganda
    return '256' + cleaned

def get_phone_provider(phone_number):
    """Determine mobile money provider from phone number"""
    formatted = format_phone_number(phone_number)
    
    if formatted.startswith('2567'):
        # Check if Airtel (2567...)
        mtn_prefixes = ['25678', '25675']  # MTN prefixes in Uganda
        if any(formatted.startswith(prefix) for prefix in mtn_prefixes):
            return 'mtn'
        return 'airtel'  # Most 2567 numbers are Airtel
    elif formatted.startswith('25678'):
        return 'mtn'
    else:
        return None  # Unknown provider

def validate_mobile_money_payment(amount):
    """Validate payment amount for mobile money"""
    min_amount = int(os.getenv('MINIMUM_PAYMENT_AMOUNT', 1000))
    max_amount = int(os.getenv('MAXIMUM_PAYMENT_AMOUNT', 1000000))
    
    if amount < min_amount:
        return False, f"Minimum payment amount is {min_amount} UGX"
    if amount > max_amount:
        return False, f"Maximum payment amount is {max_amount} UGX"
    return True, "Valid amount"

