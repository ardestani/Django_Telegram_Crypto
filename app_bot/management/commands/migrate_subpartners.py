from django.core.management.base import BaseCommand
from django.db import transaction
from app_account.models import User
from app_bot.services import NOWPaymentsService
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Migrate existing users to NOWPayments sub-partner accounts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='Migrate specific user by ID',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        user_id = options.get('user_id')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Get users without sub-partner IDs
        if user_id:
            users = User.objects.filter(id=user_id, nowpayments_sub_partner_id__isnull=True)
        else:
            users = User.objects.filter(nowpayments_sub_partner_id__isnull=True)
        
        total_users = users.count()
        self.stdout.write(f"Found {total_users} users without NOWPayments sub-partner IDs")
        
        if total_users == 0:
            self.stdout.write(self.style.SUCCESS('All users already have sub-partner IDs'))
            return
        
        nowpayments_service = NOWPaymentsService()
        success_count = 0
        error_count = 0
        
        for user in users:
            try:
                self.stdout.write(f"Processing user {user.id}: {user.telegram_full_name}")
                
                if dry_run:
                    self.stdout.write(f"  Would create sub-partner account for user {user.id}")
                    continue
                
                # Create sub-partner account
                user_data = {
                    'telegram_id': user.telegram_id,
                    'telegram_username': user.telegram_username,
                    'telegram_full_name': user.telegram_full_name,
                    'email': f"user_{user.telegram_id}@telegram.com",
                    'name': user.telegram_full_name or f"User {user.telegram_id}"
                }
                
                sub_partner_response = nowpayments_service.create_sub_partner_account(user_data)
                
                if sub_partner_response and 'result' in sub_partner_response and 'id' in sub_partner_response['result']:
                    # Update user with sub-partner ID
                    sub_partner_id = sub_partner_response['result']['id']
                    with transaction.atomic():
                        user.nowpayments_sub_partner_id = sub_partner_id
                        user.save()
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  ✓ Created sub-partner account: {sub_partner_id}"
                        )
                    )
                    success_count += 1
                else:
                    self.stdout.write(
                        self.style.ERROR(f"  ✗ Failed to create sub-partner account for user {user.id}")
                    )
                    error_count += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  ✗ Error processing user {user.id}: {e}")
                )
                error_count += 1
        
        # Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write("MIGRATION SUMMARY")
        self.stdout.write("="*50)
        self.stdout.write(f"Total users processed: {total_users}")
        self.stdout.write(f"Successful migrations: {success_count}")
        self.stdout.write(f"Failed migrations: {error_count}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("This was a dry run - no changes were made"))
        else:
            self.stdout.write(self.style.SUCCESS("Migration completed!")) 