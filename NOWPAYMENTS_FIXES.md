# NOWPayments Sub-Partner Integration Fixes

## Issues Fixed

### 1. Missing Sub-Partner ID Assignment
**Problem**: The `nowpayments_sub_partner_id` field existed in the User model but was never populated.

**Solution**: 
- Updated `save_user()` function in `app_bot/bot.py` to create NOWPayments sub-partner accounts for new users
- Added `ensure_sub_partner_account()` function to handle existing users without sub-partner IDs
- Integrated sub-partner creation into user registration flow

### 2. Users Not Appearing in NOWPayments Dashboard
**Problem**: Users were not being created as sub-partners in NOWPayments, so they didn't appear in the dashboard.

**Solution**:
- Added automatic sub-partner account creation when users register
- Updated payment creation to include sub-partner IDs
- Added comprehensive error handling and logging

### 3. API Integration Issues
**Problem**: Limited debugging information made it difficult to troubleshoot API issues.

**Solution**:
- Added detailed logging to all NOWPayments API calls
- Created test script to verify API connectivity
- Added management command for migrating existing users

## Changes Made

### 1. Updated `app_bot/bot.py`

#### New Functions Added:
- `ensure_sub_partner_account(user)`: Ensures existing users have sub-partner accounts
- Enhanced `save_user()`: Now creates sub-partner accounts for new users

#### Updated Functions:
- `start()`: Now ensures sub-partner accounts exist
- `balance()`: Now ensures sub-partner accounts exist
- `currency_selected()`: Now ensures sub-partner accounts exist before payment creation

### 2. Updated `app_bot/services.py`

#### Enhanced NOWPaymentsService:
- Added detailed logging to `create_sub_partner_account()`
- Added detailed logging to `create_payment()`
- Updated `create_payment()` to accept and use sub-partner IDs

#### Enhanced PaymentProcessor:
- Updated `create_deposit_payment()` to pass sub-partner IDs to NOWPayments

### 3. New Management Command
Created `app_bot/management/commands/migrate_subpartners.py`:
- Migrates existing users to have sub-partner accounts
- Supports dry-run mode for testing
- Supports migrating specific users by ID

### 4. Test Script
Created `test_nowpayments.py`:
- Tests NOWPayments API connectivity
- Verifies sub-partner account creation
- Tests payment creation endpoints

## How to Use

### 1. Test NOWPayments API Connection
```bash
python test_nowpayments.py
```

### 2. Migrate Existing Users (Dry Run)
```bash
python manage.py migrate_subpartners --dry-run
```

### 3. Migrate Existing Users (Actual Migration)
```bash
python manage.py migrate_subpartners
```

### 4. Migrate Specific User
```bash
python manage.py migrate_subpartners --user-id 123
```

### 5. Check User Sub-Partner IDs
```python
# In Django shell
from app_account.models import User
users_without_subpartners = User.objects.filter(nowpayments_sub_partner_id__isnull=True)
print(f"Users without sub-partner IDs: {users_without_subpartners.count()}")
```

## Environment Variables Required

Make sure these are set in your `.env` file:
```env
NOWPAYMENTS_API_KEY=your_nowpayments_api_key_here
NOWPAYMENTS_EMAIL=your_nowpayments_email_here
NOWPAYMENTS_PASSWORD=your_nowpayments_password_here
BASE_URL=https://yourdomain.com
```

**Important**: The sub-partner endpoints require JWT authentication using email and password, not API key authentication.

## NOWPayments Dashboard Integration

After implementing these fixes:

1. **New Users**: Will automatically appear in your NOWPayments dashboard as sub-partners
2. **Existing Users**: Can be migrated using the management command
3. **Payments**: Will be associated with the correct sub-partner accounts
4. **Tracking**: All user activity will be properly tracked in NOWPayments

## Troubleshooting

### 1. Authentication Issues
- Verify `NOWPAYMENTS_API_KEY` is set correctly
- Verify `NOWPAYMENTS_EMAIL` and `NOWPAYMENTS_PASSWORD` are set correctly
- Check API key permissions in NOWPayments dashboard
- Ensure your NOWPayments account supports sub-partners
- JWT tokens expire after 5 minutes - the system will automatically refresh them

### 2. Sub-Partner Creation Fails
- Check logs for detailed error messages
- Verify user data is complete (email, name, etc.)
- Ensure NOWPayments account supports sub-partners

### 3. Payment Creation Issues
- Verify sub-partner ID is assigned to user
- Check payment creation logs
- Ensure webhook URL is accessible

### 4. Users Not Appearing in Dashboard
- Run migration command for existing users
- Check if sub-partner accounts were created successfully
- Verify NOWPayments dashboard settings

## Logging

The system now provides detailed logging for:
- Sub-partner account creation attempts
- API request/response details
- Payment creation process
- Error conditions and troubleshooting information

Check your application logs for detailed information about NOWPayments API interactions.

## Verification Steps

1. **Test API Connection**: Run `python test_nowpayments.py`
2. **Check Existing Users**: Verify users have sub-partner IDs
3. **Create Test Payment**: Try creating a payment through the bot
4. **Check NOWPayments Dashboard**: Verify users and payments appear
5. **Monitor Logs**: Check for any error messages or issues

## Support

If you encounter issues:
1. Check the detailed logs for error messages
2. Run the test script to verify API connectivity
3. Use the migration command to fix existing users
4. Verify environment variables are set correctly
5. Check NOWPayments dashboard for sub-partner accounts 