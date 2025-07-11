#!/usr/bin/env python3
"""
Test JWT authentication and sub-partner creation
"""
import os
import requests
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_jwt_auth():
    """Test JWT authentication and sub-partner creation"""
    email = os.getenv('NOWPAYMENTS_EMAIL')
    password = os.getenv('NOWPAYMENTS_PASSWORD')
    base_url = 'https://api.nowpayments.io/v1'
    
    if not email or not password:
        print("❌ NOWPAYMENTS_EMAIL or NOWPAYMENTS_PASSWORD not found")
        return False
    
    print(f"Testing with email: {email}")
    print(f"Password: {'*' * len(password)}")
    
    # Step 1: Get JWT token
    print("\n1. Getting JWT token...")
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
        print(f"Login response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if 'token' in data:
                jwt_token = data['token']
                print(f"✅ JWT token obtained: {jwt_token[:20]}...")
                
                # Step 2: Create sub-partner account
                print("\n2. Creating sub-partner account...")
                bearer_headers = {
                    'Authorization': f'Bearer {jwt_token}',
                    'Content-Type': 'application/json'
                }
                
                sub_partner_data = {
                    "name": f"Test User{int(time.time())}"
                }
                
                response = requests.post(f"{base_url}/sub-partner/balance", json=sub_partner_data, headers=bearer_headers)
                print(f"Sub-partner creation status: {response.status_code}")
                print(f"Sub-partner response: {response.text}")
                
                if response.status_code == 200:
                    sub_partner_response = response.json()
                    if 'result' in sub_partner_response and 'id' in sub_partner_response['result']:
                        sub_partner_id = sub_partner_response['result']['id']
                        print(f"✅ Sub-partner created successfully!")
                        print(f"Sub-partner ID: {sub_partner_id}")
                        
                        # Step 3: Get sub-partner balance
                        print("\n3. Getting sub-partner balance...")
                        response = requests.get(f"{base_url}/sub-partner/balance/{sub_partner_id}", headers=bearer_headers)
                        print(f"Balance status: {response.status_code}")
                        print(f"Balance response: {response.text}")
                        
                        return sub_partner_id
                    else:
                        print("❌ No sub_partner_id in response")
                        return None
                else:
                    print("❌ Sub-partner creation failed")
                    return None
            else:
                print("❌ No token in login response")
                return None
        else:
            print("❌ Login failed")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    sub_partner_id = test_jwt_auth()
    if sub_partner_id:
        print(f"\n✅ Success! Sub-partner ID: {sub_partner_id}")
    else:
        print("\n❌ Failed to create sub-partner") 