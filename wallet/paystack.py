import requests
import uuid
import json
from django.conf import settings

# Get the Paystack keys from Django settings
PAYSTACK_SECRET_KEY = getattr(settings, 'PAYSTACK_SECRET_KEY', 'sk_test_your_paystack_test_key')
PAYSTACK_BASE_URL = "https://api.paystack.co"

def generate_reference():
    """Generate a unique reference for transactions"""
    return str(uuid.uuid4())

def initialize_transaction(email, amount, callback_url=None):
    """
    Initialize a payment transaction with Paystack
    
    Args:
        email (str): Customer's email address
        amount (int): Amount in kobo (multiply naira by 100)
        callback_url (str, optional): URL to redirect to after payment
        
    Returns:
        dict: Response from Paystack API
    """
    url = f"{PAYSTACK_BASE_URL}/transaction/initialize"
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    
    # Reference for tracking the transaction
    reference = generate_reference()
    
    payload = {
        "email": email,
        "amount": int(amount * 100),  # Convert to kobo (smallest currency unit)
        "reference": reference,
    }
    
    if callback_url:
        payload["callback_url"] = callback_url
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response_data = response.json()
        
        if response.status_code == 200 and response_data.get('status'):
            return {
                'status': True,
                'reference': reference,
                'authorization_url': response_data['data']['authorization_url'],
                'access_code': response_data['data']['access_code']
            }
        else:
            return {
                'status': False,
                'message': response_data.get('message', 'Transaction initialization failed')
            }
    except Exception as e:
        return {
            'status': False,
            'message': str(e)
        }

def verify_transaction(reference):
    """
    Verify a transaction using its reference
    
    Args:
        reference (str): Transaction reference
        
    Returns:
        dict: Transaction verification details
    """
    url = f"{PAYSTACK_BASE_URL}/transaction/verify/{reference}"
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response_data = response.json()
        
        if response.status_code == 200 and response_data.get('status'):
            return {
                'status': True,
                'data': response_data['data']
            }
        else:
            return {
                'status': False,
                'message': response_data.get('message', 'Transaction verification failed')
            }
    except Exception as e:
        return {
            'status': False,
            'message': str(e)
        }

def create_dedicated_account(customer_email, first_name, last_name, phone=None):
    """
    Create a dedicated virtual account for a customer
    
    Args:
        customer_email (str): Customer's email address
        first_name (str): Customer's first name
        last_name (str): Customer's last name
        phone (str, optional): Customer's phone number
        
    Returns:
        dict: Response from Paystack API
    """
    # First, check if we need to create a customer
    customer = get_or_create_customer(customer_email, first_name, last_name, phone)
    
    if not customer['status']:
        return customer
    
    customer_code = customer['data']['customer_code']
    
    # Now create dedicated account
    url = f"{PAYSTACK_BASE_URL}/dedicated_account"
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "customer": customer_code,
        "preferred_bank": "test-bank", # For test mode
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response_data = response.json()
        
        if response.status_code == 200 and response_data.get('status'):
            return {
                'status': True,
                'data': response_data['data'],
                'account_number': response_data['data']['account_number'],
                'bank_name': response_data['data']['bank']['name'],
                'account_name': response_data['data']['account_name']
            }
        else:
            return {
                'status': False,
                'message': response_data.get('message', 'Virtual account creation failed')
            }
    except Exception as e:
        return {
            'status': False,
            'message': str(e)
        }

def get_or_create_customer(email, first_name, last_name, phone=None):
    """
    Get or create a customer in Paystack
    
    Args:
        email (str): Customer's email address
        first_name (str): Customer's first name
        last_name (str): Customer's last name
        phone (str, optional): Customer's phone number
        
    Returns:
        dict: Customer details
    """
    url = f"{PAYSTACK_BASE_URL}/customer"
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    
    # First try to fetch the customer
    try:
        response = requests.get(f"{url}?email={email}", headers=headers)
        response_data = response.json()
        
        if response.status_code == 200 and response_data.get('status') and response_data['data']:
            return {
                'status': True,
                'data': response_data['data'][0],
                'message': 'Customer found'
            }
    except Exception:
        # If fetch fails, proceed to create
        pass
    
    # Create the customer
    payload = {
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
    }
    
    if phone:
        payload["phone"] = phone
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response_data = response.json()
        
        if response.status_code == 200 and response_data.get('status'):
            return {
                'status': True,
                'data': response_data['data'],
                'message': 'Customer created'
            }
        else:
            return {
                'status': False,
                'message': response_data.get('message', 'Customer creation failed')
            }
    except Exception as e:
        return {
            'status': False,
            'message': str(e)
        } 