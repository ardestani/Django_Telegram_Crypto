#!/usr/bin/env python3
"""
Test script for NOWPayments minimum amount API endpoint
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

def test_min_amount_api():
    """Test the minimum amount API endpoint"""
    
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
    
    print("🧪 Testing NOWPayments Minimum Amount API")
    print("=" * 50)
    print(f"Settings: currency_to={currency_to}, fiat_to={fiat_to}, is_fixed_rate={is_fixed_rate}, is_fee_paid_by_user={is_fee_paid_by_user}")
    print("=" * 50)
    
    # Test currencies
    test_currencies = ['btc', 'eth', 'usdt', 'ton', 'bnb', currency_to.lower()]
    
    for currency in test_currencies:
        print(f"\n📊 Testing {currency.upper()}:")
        
        try:
            params = {
                'currency_from': currency,
                'currency_to': currency_to,
                'fiat_equivalent': fiat_to,
                'is_fixed_rate': is_fixed_rate,
                'is_fee_paid_by_user': is_fee_paid_by_user
            }
            
            url = f"{base_url}/min-amount"
            print(f"   URL: {url}")
            print(f"   Params: {params}")
            
            response = requests.get(url, params=params, headers=headers)
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success: {data}")
                
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
                    print(f"   💰 Minimum Amount: ${min_amount}")
                else:
                    print(f"   ⚠️  Could not determine minimum amount from response")
                    
            else:
                print(f"   ❌ Error: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Test completed!")

if __name__ == "__main__":
    test_min_amount_api() 