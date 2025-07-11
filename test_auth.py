#!/usr/bin/env python3
"""
Simple script to test NOWPayments authentication
"""
import os
import requests
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_auth():
    """Test different authentication methods"""
    api_key = os.getenv('NOWPAYMENTS_API_KEY')
    email = os.getenv('NOWPAYMENTS_EMAIL')
    password = os.getenv('NOWPAYMENTS_PASSWORD')
    base_url = 'https://api.nowpayments.io/v1'
    
    if not api_key:
        print("❌ NOWPAYMENTS_API_KEY not found")
        return False
    
    if not email or not password:
        print("❌ NOWPAYMENTS_EMAIL or NOWPAYMENTS_PASSWORD not found")
        return False
    
    print(f"Testing API Key: {api_key[:10]}...{api_key[-10:] if len(api_key) > 20 else '***'}")
    print(f"API Key length: {len(api_key)} characters")
    print(f"Email: {email}")
    print(f"Password: {'*' * len(password)}")
    
    # Test 1: API Key authentication
    print("\n1. Testing API Key authentication...")
    api_key_headers = {
        'x-api-key': api_key,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(f"{base_url}/merchant/coins", headers=api_key_headers)
        print(f"API Key auth status: {response.status_code}")
        if response.status_code == 200:
            print("✅ API Key authentication works")
        else:
            print(f"❌ API Key auth failed: {response.text}")
    except Exception as e:
        print(f"❌ API Key auth error: {e}")
    
    # Test 2: Email/Password authentication to get JWT token
    print("\n2. Testing Email/Password authentication...")
    login_data = {
        'email': email,
        'password': password
    }
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(f"{base_url}/auth", json=login_data, headers=headers)
        print(f"Login status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if 'token' in data:
                jwt_token = data['token']
                print(f"✅ JWT token obtained: {jwt_token[:20]}...")
                
                # Test 3: Use JWT token for Bearer authentication
                print("\n3. Testing JWT Bearer authentication...")
                bearer_headers = {
                    'Authorization': f'Bearer {jwt_token}',
                    'Content-Type': 'application/json'
                }
                
                response = requests.get(f"{base_url}/merchant/coins", headers=bearer_headers)
                print(f"JWT Bearer auth status: {response.status_code}")
                if response.status_code == 200:
                    print("✅ JWT Bearer authentication works")
                else:
                    print(f"❌ JWT Bearer auth failed: {response.text}")
                    
                return jwt_token
            else:
                print("❌ No token in login response")
                return None
        else:
            print(f"❌ Login failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None
    
    # Test 4: Test sub-partner endpoint with JWT token
    print("\n4. Testing sub-partner endpoint with JWT token...")
    test_data = {
        "name": f"Test User{int(time.time())}"
    }
    
    try:
        response = requests.post(f"{base_url}/sub-partner/balance", json=test_data, headers=bearer_headers)
        print(f"Sub-partner JWT auth status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            sub_partner_data = response.json()
            if 'result' in sub_partner_data and 'id' in sub_partner_data['result']:
                print(f"✅ Sub-partner created successfully: {sub_partner_data['result']['id']}")
            else:
                print("❌ No sub_partner_id in response")
        else:
            print("❌ Sub-partner creation failed")
            
    except Exception as e:
        print(f"❌ Sub-partner JWT auth error: {e}")
    
    # Test 5: Test alternative sub-partner endpoint
    print("\n5. Testing alternative sub-partner endpoint...")
    try:
        response = requests.post(f"{base_url}/sub-partner", json=test_data, headers=bearer_headers)
        print(f"Alternative endpoint status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Alternative endpoint error: {e}")
    
    return jwt_token
    
    # Test 6: Check account status
    print("\n6. Checking account status...")
    try:
        response = requests.get(f"{base_url}/account", headers=bearer_headers)
        print(f"Account status: {response.status_code}")
        if response.status_code == 200:
            account_data = response.json()
            print(f"Account info: {account_data}")
        else:
            print(f"Account check failed: {response.text}")
    except Exception as e:
        print(f"❌ Account check error: {e}")
    
    print("\n" + "="*50)
    print("AUTHENTICATION TEST SUMMARY")
    print("="*50)
    print("If you're getting 401 errors, check:")
    print("1. API key is correct and active")
    print("2. API key has sub-partner permissions")
    print("3. Your NOWPayments account supports sub-partners")
    print("4. You're using the correct API endpoint")
    print("5. Your account is properly verified")

if __name__ == "__main__":
    test_auth() 