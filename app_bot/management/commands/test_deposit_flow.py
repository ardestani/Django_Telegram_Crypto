from django.core.management.base import BaseCommand
from app_account.models import User
from app_bot.services import PaymentProcessor, NOWPaymentsService
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test the complete NOWPayments deposit flow'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Telegram user ID to test with'
        )
        parser.add_argument(
            '--amount',
            type=float,
            default=10.0,
            help='Amount to test with (default: 10.0)'
        )
        parser.add_argument(
            '--currency',
            type=str,
            default='btc',
            help='Currency to test with (default: btc)'
        )

    def handle(self, *args, **options):
        user_id = options['user_id']
        amount = options['amount']
        currency = options['currency'].lower()

        self.stdout.write(
            self.style.SUCCESS(f'Testing NOWPayments deposit flow with amount=${amount}, currency={currency.upper()}')
        )

        try:
            # Get or create test user
            if user_id:
                try:
                    user = User.objects.get(telegram_id=user_id)
                    self.stdout.write(f'Using existing user: {user.telegram_full_name}')
                except User.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(f'User with Telegram ID {user_id} not found')
                    )
                    return
            else:
                # Create a test user
                user = User.objects.create(
                    username=f"test_user_{user_id or 'flow'}",
                    telegram_id=user_id or 999999,
                    telegram_username="test_user",
                    telegram_full_name="Test User",
                    is_active=True
                )
                self.stdout.write(f'Created test user: {user.telegram_full_name}')

            # Initialize services
            processor = PaymentProcessor()
            nowpayments = NOWPaymentsService()

            # Get NOWPayments settings from Django
            from django.conf import settings
            currency_to = getattr(settings, 'currency_to', 'BNBBSC')
            fiat_to = getattr(settings, 'fiat_to', 'USD')
            is_fixed_rate = getattr(settings, 'is_fixed_rate', False)
            is_fee_paid_by_user = getattr(settings, 'is_fee_paid_by_user', False)
            
            self.stdout.write(f"NOWPayments Settings: currency_to={currency_to}, fiat_to={fiat_to}, is_fixed_rate={is_fixed_rate}, is_fee_paid_by_user={is_fee_paid_by_user}")

            # Step 1: Test minimum payment amount
            self.stdout.write('\n1. Testing minimum payment amount...')
            min_amount_data = nowpayments.get_minimum_payment_amount(currency)
            if min_amount_data:
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
                
                if min_amount is not None:
                    self.stdout.write(f'   Minimum amount for {currency.upper()}: ${min_amount}')
                    self.stdout.write(f'   Full response: {min_amount_data}')
                    
                    if amount < min_amount:
                        self.stdout.write(
                            self.style.WARNING(f'   Test amount ${amount} is below minimum ${min_amount}')
                        )
                        return
                else:
                    self.stdout.write(
                        self.style.WARNING(f'   Could not determine minimum amount from response: {min_amount_data}')
                    )
            else:
                self.stdout.write(
                    self.style.WARNING('   Could not get minimum amount from NOWPayments')
                )

            # Step 2: Test estimated price
            self.stdout.write('\n2. Testing estimated price...')
            estimated_data = nowpayments.get_estimated_price(amount, currency)
            if estimated_data:
                estimated_amount = estimated_data.get('estimated_amount', 0)
                self.stdout.write(f'   Estimated {currency.upper()} amount: {estimated_amount}')
            else:
                self.stdout.write(
                    self.style.WARNING('   Could not get estimated price from NOWPayments')
                )

            # Step 3: Test payment validation
            self.stdout.write('\n3. Testing payment validation...')
            is_valid, estimated_data, error_message = processor.validate_deposit_request(amount, currency)
            if is_valid:
                self.stdout.write(
                    self.style.SUCCESS('   Payment validation passed')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'   Payment validation failed: {error_message}')
                )
                return

            # Step 4: Test payment creation
            self.stdout.write('\n4. Testing payment creation...')
            payment, payment_data, error_message = processor.create_deposit_payment(user, amount, currency)
            if payment:
                self.stdout.write(
                    self.style.SUCCESS(f'   Payment created successfully: {payment.payment_id}')
                )
                self.stdout.write(f'   NOWPayments ID: {payment.nowpayments_id}')
                self.stdout.write(f'   Payment address: {payment.payment_address}')
                self.stdout.write(f'   Crypto amount: {payment.crypto_amount} {payment.currency.upper()}')
            else:
                self.stdout.write(
                    self.style.ERROR(f'   Payment creation failed: {error_message}')
                )
                return

            # Step 5: Test payment status checking
            self.stdout.write('\n5. Testing payment status checking...')
            status_data, error_message = processor.get_payment_status_manual(payment.payment_id)
            if status_data:
                self.stdout.write(
                    self.style.SUCCESS(f'   Payment status: {status_data.get("payment_status", "unknown")}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'   Could not get payment status: {error_message}')
                )

            # Step 6: Test payments list
            self.stdout.write('\n6. Testing payments list...')
            payments_data, error_message = processor.get_payments_list(limit=5)
            if payments_data:
                local_count = len(payments_data['local_payments'])
                self.stdout.write(f'   Local payments count: {local_count}')
                if payments_data['nowpayments_payments']:
                    nowpayments_count = len(payments_data['nowpayments_payments'])
                    self.stdout.write(f'   NOWPayments payments count: {nowpayments_count}')
                else:
                    self.stdout.write('   Could not get NOWPayments payments list')
            else:
                self.stdout.write(
                    self.style.WARNING(f'   Could not get payments list: {error_message}')
                )

            self.stdout.write(
                self.style.SUCCESS('\n✅ NOWPayments deposit flow test completed successfully!')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Test failed with error: {e}')
            )
            logger.error(f'Test failed: {e}') 