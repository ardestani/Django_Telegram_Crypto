#!/usr/bin/env python3
"""
Debug script to compare minimum amount API calls with Postman
"""

import os
import django
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lottolite.settings')
django.setup()

from django.conf import settings

def debug_min_amount_api():
    """Debug the minimum amount API call"""
    
    api_key = os.getenv('NOWPAYMENTS_API_KEY')
    if not api_key:
        print("❌ NOWPAYMENTS_API_KEY not found in environment variables")
        return
    
    # Get NOWPayments settings from Django
    currency_to = getattr(settings, 'currency_to', 'BNBBSC')
    fiat_to = getattr(settings, 'fiat_to', 'USD')
    is_fixed_rate = getattr(settings, 'is_fixed_rate', False)
    is_fee_paid_by_user = getattr(settings, 'is_fee_paid_by_user', False)
    
    base_url = 'https://api.nowpayments.io/v1'
    headers = {
        'x-api-key': api_key,
        'Content-Type': 'application/json'
    }
    
    print("🔍 Debugging NOWPayments Minimum Amount API")
    print("=" * 60)
    print(f"Django Settings:")
    print(f"  currency_to: {currency_to}")
    print(f"  fiat_to: {fiat_to}")
    print(f"  is_fixed_rate: {is_fixed_rate} (type: {type(is_fixed_rate)})")
    print(f"  is_fee_paid_by_user: {is_fee_paid_by_user} (type: {type(is_fee_paid_by_user)})")
    print("=" * 60)
    
    # Test currencies
    test_currencies = ['btc', 'eth', 'usdt', 'ton', 'bnb']
    
    for currency in test_currencies:
        print(f"\n📊 Testing {currency.upper()}:")
        
        # Current implementation parameters
        current_params = {
            'currency_from': currency,
            'currency_to': currency_to,
            'fiat_equivalent': fiat_to,
            'is_fixed_rate': is_fixed_rate,
            'is_fee_paid_by_user': is_fee_paid_by_user
        }
        
        print(f"   Current Implementation Parameters:")
        for key, value in current_params.items():
            print(f"     {key}: {value} (type: {type(value)})")
        
        # Alternative parameter formats to test
        test_cases = [
            {
                'name': 'Current Implementation',
                'params': current_params
            },
            {
                'name': 'Postman Style (string booleans)',
                'params': {
                    'currency_from': currency,
                    'currency_to': currency_to,
                    'fiat_equivalent': fiat_to,
                    'is_fixed_rate': str(is_fixed_rate).lower(),
                    'is_fee_paid_by_user': str(is_fee_paid_by_user).lower()
                }
            },
            {
                'name': 'Uppercase Fiat',
                'params': {
                    'currency_from': currency,
                    'currency_to': currency_to,
                    'fiat_equivalent': fiat_to.upper(),
                    'is_fixed_rate': is_fixed_rate,
                    'is_fee_paid_by_user': is_fee_paid_by_user
                }
            },
            {
                'name': 'Minimal Parameters',
                'params': {
                    'currency_from': currency,
                    'currency_to': currency_to
                }
            }
        ]
        
        for test_case in test_cases:
            print(f"\n   🧪 {test_case['name']}:")
            print(f"     Parameters: {test_case['params']}")
            
            try:
                url = f"{base_url}/min-amount"
                response = requests.get(url, params=test_case['params'], headers=headers)
                
                print(f"     Status Code: {response.status_code}")
                print(f"     URL: {response.url}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"     ✅ Response: {data}")
                    
                    # Try to extract minimum amount
                    min_amount = None
                    if 'min_amount' in data:
                        min_amount = data['min_amount']
                    elif 'min_amount_usd' in data:
                        min_amount = data['min_amount_usd']
                    elif 'min_amount_fiat' in data:
                        min_amount = data['min_amount_fiat']
                    else:
                        for key, value in data.items():
                            if 'min' in key.lower() and isinstance(value, (int, float)):
                                min_amount = value
                                break
                    
                    if min_amount is not None:
                        print(f"     💰 Minimum Amount: ${min_amount}")
                    else:
                        print(f"     ⚠️  Could not determine minimum amount")
                        
                else:
                    print(f"     ❌ Error: {response.text}")
                    
            except Exception as e:
                print(f"     ❌ Exception: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Debug completed!")
    print("\n💡 Compare the results above with your Postman request")
    print("   Look for differences in parameter values, types, or order")

if __name__ == "__main__":
    debug_min_amount_api() 