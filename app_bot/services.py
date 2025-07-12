import os
import requests
import qrcode
import io
import base64
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class NOWPaymentsService:
    """Service class for NOWPayments API integration"""
    
    def __init__(self):
        self.api_key = os.getenv('NOWPAYMENTS_API_KEY')
        self.base_url = 'https://api.nowpayments.io/v1'
        self.jwt_token = None
        
        # Get NOWPayments settings from Django settings
        from django.conf import settings
        self.currency_from = getattr(settings, 'currency_from', 'BNBBSC')
        self.currency_to = getattr(settings, 'currency_to', 'BNBBSC')
        self.fiat_to = getattr(settings, 'fiat_to', 'USD')
        self.is_fixed_rate = getattr(settings, 'is_fixed_rate', False)
        self.is_fee_paid_by_user = getattr(settings, 'is_fee_paid_by_user', False)
        
        # Debug API key (show first and last few characters)
        if self.api_key:
            print(f"API Key found: {self.api_key[:10]}...{self.api_key[-10:] if len(self.api_key) > 20 else '***'}")
        else:
            print("WARNING: NOWPAYMENTS_API_KEY not found in environment variables")
        
        print(f"NOWPayments Settings: currency_from={self.currency_from}, currency_to={self.currency_to}, fiat_to={self.fiat_to}, is_fixed_rate={self.is_fixed_rate}, is_fee_paid_by_user={self.is_fee_paid_by_user}")
        
        # Different endpoints use different authentication methods
        self.api_key_headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json'
        }
        
        print(f"API Key Headers: {self.api_key_headers}")
    
    def get_jwt_token(self):
        """Get JWT token for Bearer authentication"""
        if self.jwt_token:
            return self.jwt_token
            
        try:
            # Get email and password from environment
            email = os.getenv('NOWPAYMENTS_EMAIL')
            password = os.getenv('NOWPAYMENTS_PASSWORD')
            
            if not email or not password:
                print("NOWPAYMENTS_EMAIL and NOWPAYMENTS_PASSWORD must be set in environment variables")
                return None
            
            # Login to get JWT token using email and password
            login_data = {
                'email': email,
                'password': password
            }
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            print(f"Logging in with email: {email}")
            response = requests.post(f"{self.base_url}/auth", json=login_data, headers=headers)
            print(f"Login response status: {response.status_code}")
            print(f"Login response: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                if 'token' in data:
                    self.jwt_token = data['token']
                    print(f"JWT token obtained: {self.jwt_token[:20]}...")
                    return self.jwt_token
                else:
                    print("No token in login response")
                    return None
            else:
                print(f"Login failed: {response.text}")
                return None
                
        except Exception as e:
            print(f"Error getting JWT token: {e}")
            return None
    
    def get_bearer_headers(self):
        """Get headers with valid JWT token"""
        token = self.get_jwt_token()
        if token:
            return {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        else:
            print("Failed to get JWT token for Bearer authentication")
            return None
    
    def get_available_currencies(self):
        """Get list of available cryptocurrencies from merchant coins endpoint"""
        try:
            response = requests.get(f"{self.base_url}/merchant/coins", headers=self.api_key_headers)
            response.raise_for_status()
            data = response.json()
            
            # Extract the selectedCurrencies list from the response
            if 'selectedCurrencies' in data:
                return data['selectedCurrencies']
            else:
                print("Unexpected response format from merchant/coins endpoint")
                return None
                
        except requests.RequestException as e:
            print(f"Error getting merchant coins: {e}")
            return None
    
    def get_currency_info(self, currency):
        """Get information about a specific currency"""
        try:
            response = requests.get(f"{self.base_url}/currencies/{currency}", headers=self.api_key_headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error getting currency info: {e}")
            return None
    
    def get_estimated_price(self, amount, currency_to):
        """Get estimated price for currency conversion"""
        try:
            params = {
                'amount': amount,
                'currency_from': self.fiat_to.lower(),
                'currency_to': currency_to,
            }
            print(f"Estimated price API call parameters: {params}")
            response = requests.get(f"{self.base_url}/estimate", params=params, headers=self.api_key_headers)
            response.raise_for_status()
            result = response.json()
            print(f"Estimated price API response: {result}")
            return result
        except requests.RequestException as e:
            print(f"Error getting estimated price: {e}")
            return None
    
    def create_payment(self, amount, currency_from, currency_to, order_id, order_description, sub_partner_id=None):
        """Create a new payment"""
        try:
            data = {
                'price_amount': amount,
                'price_currency': currency_from,
                'pay_currency': currency_to,
                'order_id': str(order_id),
                'order_description': order_description,
                'ipn_callback_url': f"{os.getenv('BASE_URL', 'http://localhost:8000')}/api/payment/webhook/",
                'is_fixed_rate': str(self.is_fixed_rate).lower(),
                'is_fee_paid_by_user': str(self.is_fee_paid_by_user).lower()
            }
            
            # Add sub-partner ID if provided
            if sub_partner_id:
                data['sub_partner_id'] = sub_partner_id
                print(f"Using sub-partner ID: {sub_partner_id}")
            else:
                print("No sub-partner ID provided")
            
            print(f"Creating payment with data: {data}")
            print(f"API URL: {self.base_url}/payment")
            
            response = requests.post(f"{self.base_url}/payment", json=data, headers=self.api_key_headers)
            
            print(f"Payment creation response status: {response.status_code}")
            print(f"Payment creation response content: {response.text}")
            
            response.raise_for_status()
            result = response.json()
            print(f"Payment creation result: {result}")
            return result
        except requests.RequestException as e:
            print(f"Error creating payment: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response content: {e.response.text}")
            return None
    
    def get_payment_status(self, payment_id):
        """Get payment status"""
        try:
            response = requests.get(f"{self.base_url}/payment/{payment_id}", headers=self.api_key_headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error getting payment status: {e}")
            return None
    
    def get_minimum_payment_amount(self, currency_from):
        """Get minimum payment amount for currency pair"""
        try:
            params = {
                'currency_from': currency_from,
                'currency_to': self.currency_to,
                'fiat_equivalent': self.fiat_to,
                'is_fixed_rate': str(self.is_fixed_rate).lower(),
                'is_fee_paid_by_user': str(self.is_fee_paid_by_user).lower()
            }
            print(f"Minimum amount API call parameters: {params}")
            response = requests.get(f"{self.base_url}/min-amount", params=params, headers=self.api_key_headers)
            response.raise_for_status()
            result = response.json()
            print(f"Minimum amount API response: {result}")
            return result
        except requests.RequestException as e:
            print(f"Error getting minimum amount: {e}")
            return None
    
    def create_sub_partner_account(self, user_data):
        """Create a new sub-partner account for user"""
        try:
            # Create unique name by combining user name with Telegram ID
            base_name = user_data.get('name', user_data.get('telegram_full_name', 'Unknown User'))
            telegram_id = user_data.get('telegram_id', 'unknown')
            unique_name = f"{base_name}{telegram_id}"
            
            data = {
                "name": unique_name
            }
            
            print(f"Creating sub-partner account with data: {data}")
            print(f"API URL: {self.base_url}/sub-partner/balance")
            
            # Get Bearer headers with JWT token
            bearer_headers = self.get_bearer_headers()
            if not bearer_headers:
                print("Failed to get Bearer headers")
                return None
            
            print(f"Bearer headers: {bearer_headers}")
            
            # Try the sub-partner endpoint with Bearer authentication
            response = requests.post(f"{self.base_url}/sub-partner/balance", json=data, headers=bearer_headers)
            
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {response.headers}")
            print(f"Response content: {response.text}")
            
            # If Bearer auth fails, try with API key auth
            if response.status_code == 401:
                print("Bearer auth failed, trying with API key auth...")
                response = requests.post(f"{self.base_url}/sub-partner/balance", json=data, headers=self.api_key_headers)
                print(f"API Key auth response status: {response.status_code}")
                print(f"API Key auth response content: {response.text}")
                
                # If that also fails, try alternative endpoint
                if response.status_code == 401:
                    print("API key auth also failed, trying alternative endpoint...")
                    response = requests.post(f"{self.base_url}/sub-partner", json=data, headers=self.api_key_headers)
                    print(f"Alternative endpoint response status: {response.status_code}")
                    print(f"Alternative endpoint response content: {response.text}")
                    
                # If JWT token expired, try to get a new one
                elif response.status_code == 403 and "expired" in response.text.lower():
                    print("JWT token expired, trying to get new token...")
                    self.jwt_token = None  # Reset token
                    bearer_headers = self.get_bearer_headers()
                    if bearer_headers:
                        response = requests.post(f"{self.base_url}/sub-partner/balance", json=data, headers=bearer_headers)
                        print(f"New token response status: {response.status_code}")
                        print(f"New token response content: {response.text}")
            
            response.raise_for_status()
            result = response.json()
            print(f"Sub-partner creation result: {result}")
            return result
        except requests.RequestException as e:
            print(f"Error creating sub-partner account: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response content: {e.response.text}")
            return None
    
    def get_sub_partner_balance(self, sub_partner_id):
        """Get sub-partner balance"""
        try:
            bearer_headers = self.get_bearer_headers()
            if not bearer_headers:
                print("Failed to get Bearer headers for sub-partner balance")
                return None
                
            response = requests.get(f"{self.base_url}/sub-partner/balance/{sub_partner_id}", headers=bearer_headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error getting sub-partner balance: {e}")
            return None

    def generate_qr_code(self, payment_address, amount=None, currency=None):
        """Generate QR code for payment address"""
        try:
            # Create QR code data
            qr_data = payment_address
            if amount and currency:
                # Round amount to 8 decimal places for QR code
                rounded_amount = round(float(amount), 8)
                qr_data = f"{currency}:{payment_address}?amount={rounded_amount}"
            
            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return image_base64
        except Exception as e:
            print(f"Error generating QR code: {e}")
            return None

    def get_payments_list(self, limit=50, offset=0):
        """Get list of payments made to account (Step 9)"""
        try:
            params = {
                'limit': limit,
                'offset': offset
            }
            response = requests.get(f"{self.base_url}/payment", params=params, headers=self.api_key_headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error getting payments list: {e}")
            return None


class PaymentProcessor:
    """Payment processing logic following NOWPayments official deposit flow"""
    
    def __init__(self):
        self.nowpayments = NOWPaymentsService()
    
    def validate_deposit_request(self, amount_usd, currency):
        """
        Step 4-5: Validate minimum payment amount and get estimated price
        Returns: (is_valid, estimated_data, error_message)
        """
        try:
            # Step 4: Get minimum payment amount for the currency pair
            min_amount_data = self.nowpayments.get_minimum_payment_amount(currency.lower())
            
            if not min_amount_data:
                return False, None, f"Unable to get minimum amount for {currency.upper()}"
            
            # Handle different possible response formats
            min_amount = None
            if 'min_amount' in min_amount_data:
                min_amount = min_amount_data['min_amount']
            elif 'min_amount_usd' in min_amount_data:
                min_amount = min_amount_data['min_amount_usd']
            elif 'min_amount_fiat' in min_amount_data:
                min_amount = min_amount_data['min_amount_fiat']
            else:
                # Try to find any field that might contain the minimum amount
                for key, value in min_amount_data.items():
                    if 'min' in key.lower() and isinstance(value, (int, float)):
                        min_amount = value
                        break
            
            if min_amount is None:
                print(f"Could not find minimum amount in response: {min_amount_data}")
                return False, None, f"Unable to determine minimum amount for {currency.upper()}"
            
            print(f"Minimum amount for {currency.upper()}: ${min_amount}")
            
            # Convert min_amount to float for comparison
            try:
                min_amount_float = float(min_amount)
            except (ValueError, TypeError):
                print(f"Could not convert min_amount '{min_amount}' to float")
                return False, None, f"Invalid minimum amount format for {currency.upper()}"
            
            # Check if user amount meets minimum requirement
            if amount_usd < min_amount_float:
                return False, None, f"Amount ${amount_usd} is below minimum required amount of ${min_amount_float} for {currency.upper()}"
            
            # Step 5: Get estimated price and validate
            estimated_data = self.nowpayments.get_estimated_price(amount_usd, currency.lower())
            
            if not estimated_data:
                return False, None, f"Unable to get estimated price for {currency.upper()}"
            
            estimated_amount = estimated_data.get('estimated_amount', 0)
            print(f"Estimated {currency.upper()} amount: {estimated_amount}")
            
            # Convert estimated_amount to float for comparison
            try:
                estimated_amount_float = float(estimated_amount)
            except (ValueError, TypeError):
                print(f"Could not convert estimated_amount '{estimated_amount}' to float")
                return False, None, f"Invalid estimated amount format for {currency.upper()}"
            
            # Validate that estimated amount is larger than minimum
            if estimated_amount_float < min_amount_float:
                return False, None, f"Estimated amount {estimated_amount_float} {currency.upper()} is below minimum required amount of {min_amount_float} {currency.upper()}"
            
            return True, estimated_data, None
            
        except Exception as e:
            print(f"Error validating deposit request: {e}")
            return False, None, f"Error validating deposit request: {str(e)}"
    
    def create_deposit_payment(self, user, amount_usd, currency):
        """
        Complete NOWPayments deposit flow implementation
        Steps:
        1. Registration and user account creation (handled in bot.py)
        2. Ask for deposit amount and currency (handled in bot.py)
        3. Validate minimum payment amount
        4. Get estimated price and validate
        5. Create payment with NOWPayments
        6. Return payment details for user
        """
        from .models import Payment
        
        print(f"Creating deposit payment: User={user.telegram_full_name}, Amount=${amount_usd}, Currency={currency}")
        
        # Step 3-5: Validate minimum amount and get estimated price
        is_valid, estimated_data, error_message = self.validate_deposit_request(amount_usd, currency)
        
        if not is_valid:
            print(f"Deposit validation failed: {error_message}")
            return None, None, error_message
        
        # Create payment record with estimated data
        payment = Payment.objects.create(
            user=user,
            amount_usd=amount_usd,
            currency=currency,
            expires_at=timezone.now() + timedelta(hours=24)  # 24 hour expiry
        )
        
        try:
            # Step 6: Create NOWPayments payment (POST Deposit with payment)
            payment_data = self.nowpayments.create_payment(
                amount=amount_usd,
                currency_from=currency.lower(),
                currency_to=self.nowpayments.fiat_to.lower(),
                order_id=payment.payment_id,
                order_description=f"Wallet deposit for {user.telegram_full_name}",
                sub_partner_id=user.nowpayments_sub_partner_id
            )
            
            if payment_data and 'payment_id' in payment_data:
                # Update payment record with NOWPayments data
                payment.nowpayments_id = payment_data['payment_id']
                payment.payment_address = payment_data.get('pay_address')
                payment.payment_extra_id = payment_data.get('payin_extra_id')
                payment.crypto_amount = Decimal(payment_data.get('pay_amount', 0))
                payment.save()
                
                print(f"Payment created successfully: {payment.payment_id} -> NOWPayments ID: {payment.nowpayments_id}")
                return payment, payment_data, None
            else:
                payment.delete()
                error_msg = "Failed to create payment with NOWPayments"
                print(error_msg)
                return None, None, error_msg
                
        except Exception as e:
            payment.delete()
            error_msg = f"Error creating payment: {str(e)}"
            print(error_msg)
            return None, None, error_msg
    
    def get_payment_status_manual(self, payment_id):
        """
        Step 8: Manual payment status checking (alternative to webhooks)
        """
        try:
            payment = Payment.objects.get(payment_id=payment_id)
            
            if not payment.nowpayments_id:
                return None, "Payment not linked to NOWPayments"
            
            # Get status from NOWPayments API
            status_data = self.nowpayments.get_payment_status(payment.nowpayments_id)
            
            if status_data:
                # Update local payment status
                payment_status = status_data.get('payment_status', 'pending')
                payment.status = payment_status.upper()
                payment.save()
                
                return status_data, None
            else:
                return None, "Unable to get payment status from NOWPayments"
                
        except Payment.DoesNotExist:
            return None, "Payment not found"
        except Exception as e:
            print(f"Error getting payment status: {e}")
            return None, f"Error: {str(e)}"
    
    def get_payments_list(self, limit=50, offset=0):
        """
        Step 9: Get list of payments made to account
        This would typically be called from admin interface or for reporting
        """
        try:
            # Get payments from database (local payments)
            payments = Payment.objects.all().order_by('-created_at')[offset:offset+limit]
            
            # Also get payments from NOWPayments API
            nowpayments_payments = self.nowpayments.get_payments_list(limit, offset)
            
            return {
                'local_payments': payments,
                'nowpayments_payments': nowpayments_payments
            }, None
        except Exception as e:
            print(f"Error getting payments list: {e}")
            return None, f"Error: {str(e)}"
    
    def process_payment_webhook(self, payment_data):
        """Process payment webhook from NOWPayments (Step 7)"""
        from .models import Payment, Wallet
        
        payment_id = payment_data.get('payment_id')
        payment_status = payment_data.get('payment_status')
        
        try:
            payment = Payment.objects.get(nowpayments_id=payment_id)
            
            # Update payment status
            payment.status = payment_status.upper()
            payment.save()
            
            # Process completed payments
            if payment_status in ['finished', 'confirmed'] and not payment.is_processed:
                # Add funds to user wallet
                wallet = payment.user.wallet
                wallet.add_funds(payment.amount_usd, "DEPOSIT")
                
                # Mark payment as processed
                payment.is_processed = True
                payment.save()
                
                print(f"Payment {payment.payment_id} processed successfully. User wallet topped up with ${payment.amount_usd}")
                return True, payment
            
            return True, payment
            
        except Payment.DoesNotExist:
            print(f"Payment with NOWPayments ID {payment_id} not found in database")
            return False, None
    
    def get_payment_info(self, payment):
        """Get payment information for display"""
        qr_code = self.nowpayments.generate_qr_code(
            payment.payment_address,
            payment.crypto_amount,
            payment.currency
        )
        
        return {
            'payment': payment,
            'qr_code': qr_code,
            'payment_address': payment.payment_address,
            'crypto_amount': round(float(payment.crypto_amount), 8) if payment.crypto_amount else None,
            'currency': payment.currency.upper(),
            'expires_at': payment.expires_at
        } 