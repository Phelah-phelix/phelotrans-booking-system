import requests
import json
import base64
from datetime import datetime
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class MpesaService:
    def __init__(self):
        # Use the correct settings variable names
        self.consumer_key = getattr(settings, 'DARAJAA_CONSUMER_KEY', '')
        self.consumer_secret = getattr(settings, 'DARAJAA_CONSUMER_SECRET', '')
        self.passkey = getattr(settings, 'DARAJAA_PASSKEY', '')
        self.shortcode = getattr(settings, 'DARAJAA_SHORTCODE', '174379')
        self.environment = getattr(settings, 'DARAJAA_ENVIRONMENT', 'sandbox')
        
        if self.environment == 'sandbox':
            self.base_url = 'https://sandbox.safaricom.co.ke'
        else:
            self.base_url = 'https://api.safaricom.co.ke'
    
    def get_access_token(self):
        """Get OAuth access token"""
        if not self.consumer_key or not self.consumer_secret:
            logger.error("Consumer key or secret not configured")
            return None
            
        url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        
        # Encode credentials
        credentials = f"{self.consumer_key}:{self.consumer_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {encoded_credentials}'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            result = response.json()
            return result.get('access_token')
        except Exception as e:
            logger.error(f"Failed to get access token: {str(e)}")
            return None
    
    def stk_push(self, phone_number, amount, account_reference, transaction_desc, callback_url):
        """Initiate STK Push"""
        if not self.consumer_key or not self.consumer_secret:
            return {'error': 'M-Pesa not configured. Please add Daraja credentials in settings.'}
        
        access_token = self.get_access_token()
        if not access_token:
            return {'error': 'Failed to get access token. Check your consumer key and secret.'}
        
        # Format phone number (remove 0 or +254, add 254)
        if phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        elif phone_number.startswith('+'):
            phone_number = phone_number[1:]
        
        # Generate timestamp
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        
        # Generate password
        password_str = f"{self.shortcode}{self.passkey}{timestamp}"
        password = base64.b64encode(password_str.encode()).decode()
        
        # Prepare request payload
        payload = {
            'BusinessShortCode': self.shortcode,
            'Password': password,
            'Timestamp': timestamp,
            'TransactionType': 'CustomerPayBillOnline',
            'Amount': int(amount),
            'PartyA': phone_number,
            'PartyB': self.shortcode,
            'PhoneNumber': phone_number,
            'CallBackURL': callback_url,
            'AccountReference': account_reference[:12],  # Max 12 characters
            'TransactionDesc': transaction_desc[:13]  # Max 13 characters
        }
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"STK Push failed: {str(e)}")
            return {'error': str(e)}
    
    def query_status(self, checkout_request_id):
        """Query STK Push status"""
        if not self.consumer_key or not self.consumer_secret:
            return {'error': 'M-Pesa not configured'}
            
        access_token = self.get_access_token()
        if not access_token:
            return {'error': 'Failed to get access token'}
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password_str = f"{self.shortcode}{self.passkey}{timestamp}"
        password = base64.b64encode(password_str.encode()).decode()
        
        payload = {
            'BusinessShortCode': self.shortcode,
            'Password': password,
            'Timestamp': timestamp,
            'CheckoutRequestID': checkout_request_id
        }
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}/mpesa/stkpushquery/v1/query"
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Query failed: {str(e)}")
            return {'error': str(e)}
