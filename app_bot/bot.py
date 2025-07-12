import os
import django
import logging
from decimal import Decimal
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup Django if not already configured
try:
    django.setup()
except Exception:
    pass  # Django might already be configured

from app_account.models import User
from app_bot.models import Wallet, Payment, Transaction
from app_bot.services import PaymentProcessor, NOWPaymentsService
from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
from asgiref.sync import sync_to_async
import base64
import io

BOT_TOKEN = os.getenv('BOT_TOKEN')
BASE_URL = os.getenv('BASE_URL')

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Conversation states for payment flow
CHOOSING_AMOUNT, CHOOSING_CURRENCY = range(2)

@sync_to_async
def save_user(user):
    # Try to find existing user by telegram_id first
    try:
        theUser = User.objects.get(telegram_id=user.id)
        # Update user info if it has changed
        if theUser.telegram_username != user.username or theUser.telegram_full_name != user.full_name:
            theUser.telegram_username = user.username
            theUser.telegram_full_name = user.full_name
            theUser.save()
        created = False
    except User.DoesNotExist:
        # Create new user
        theUser = User.objects.create(
            username=f"user_{user.id}",  # Generate unique username
            telegram_id=user.id,
            telegram_username=user.username,
            telegram_full_name=user.full_name,
            is_active=True,
            is_admin=False,
        )
        created = True
    
    if created:
        # Create a wallet for the new user
        Wallet.objects.create(user=theUser, balance=Decimal('0.00'))
        
        # Create NOWPayments sub-partner account
        try:
            nowpayments_service = NOWPaymentsService()
            user_data = {
                'telegram_id': user.id,
                'telegram_username': user.username,
                'telegram_full_name': user.full_name,
                'email': f"user_{user.id}@telegram.com",
                'name': user.full_name or f"User {user.id}"
            }
            
            sub_partner_response = nowpayments_service.create_sub_partner_account(user_data)
            
            if sub_partner_response and 'result' in sub_partner_response and 'id' in sub_partner_response['result']:
                # Update user with sub-partner ID
                sub_partner_id = sub_partner_response['result']['id']
                theUser.nowpayments_sub_partner_id = sub_partner_id
                theUser.save()
                logger.info(f"Created NOWPayments sub-partner account for user {user.id}: {sub_partner_id}")
            else:
                logger.warning(f"Failed to create NOWPayments sub-partner account for user {user.id}")
                
        except Exception as e:
            logger.error(f"Error creating NOWPayments sub-partner account for user {user.id}: {e}")
    
    return theUser

@sync_to_async
def get_user_wallet(user):
    """Get or create user wallet"""
    wallet, created = Wallet.objects.get_or_create(user=user, defaults={'balance': Decimal('0.00')})
    return wallet

@sync_to_async
def get_available_currencies():
    """Get available cryptocurrencies from NOWPayments"""
    service = NOWPaymentsService()
    return service.get_available_currencies()

@sync_to_async
def create_payment(user, amount, currency):
    """Create a payment for user following NOWPayments official flow"""
    processor = PaymentProcessor()
    return processor.create_deposit_payment(user, amount, currency)

@sync_to_async
def get_user_payments(user):
    """Get user's payment history"""
    return Payment.objects.filter(user=user).order_by('-created_at')

@sync_to_async
def get_user_transactions(user):
    """Get user's transaction history"""
    return user.wallet.transactions.all()[:10]  # Last 10 transactions

@sync_to_async
def get_user_transaction_count(user):
    """Get user's transaction count"""
    return user.wallet.transactions.count()

@sync_to_async
def ensure_sub_partner_account(user):
    """Ensure user has a NOWPayments sub-partner account"""
    if not user.nowpayments_sub_partner_id:
        try:
            nowpayments_service = NOWPaymentsService()
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
                user.nowpayments_sub_partner_id = sub_partner_id
                user.save()
                logger.info(f"Created NOWPayments sub-partner account for existing user {user.telegram_id}: {sub_partner_id}")
                return True
            else:
                logger.warning(f"Failed to create NOWPayments sub-partner account for existing user {user.telegram_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating NOWPayments sub-partner account for existing user {user.telegram_id}: {e}")
            return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await save_user(update.effective_user)
    
    # Ensure user has NOWPayments sub-partner account
    await ensure_sub_partner_account(user)
    
    welcome_message = f"""
🚀 Welcome to CryptoPayment Bot, {user.telegram_full_name}! 🚀

Your secure cryptocurrency payment solution powered by Django and Telegram.

Available commands:
/balance - Check your wallet balance
/deposit - Add funds to your wallet (cryptocurrency)
/transactions - View transaction history
/payments - View payment history
/help - Show this help message

Get started by checking your balance with /balance!
    """
    
    await update.message.reply_text(welcome_message)

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await save_user(update.effective_user)
    
    # Ensure user has NOWPayments sub-partner account
    await ensure_sub_partner_account(user)
    
    wallet = await get_user_wallet(user)
    transaction_count = await get_user_transaction_count(user)
    
    balance_message = f"""
💰 Wallet Balance 💰

Current Balance: ${wallet.balance}
Total Transactions: {transaction_count}

Use /transactions to view your transaction history.
Use /deposit to add funds to your wallet.
    """
    
    await update.message.reply_text(balance_message)

async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start deposit flow"""
    await update.message.reply_text(
        "💳 Deposit Funds 💳\n\n"
        "Please enter the amount you want to deposit (in USD):\n"
        "Minimum: $5.00\n"
        "Maximum: $1000.00\n\n"
        "Example: 50"
    )
    return CHOOSING_AMOUNT

async def amount_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle amount input and show currency options"""
    try:
        amount = float(update.message.text)
        if amount < 5 or amount > 1000:
            await update.message.reply_text(
                "❌ Invalid amount! Please enter a value between $5.00 and $1000.00"
            )
            return CHOOSING_AMOUNT
        
        context.user_data['deposit_amount'] = amount
        
        # Get available currencies
        currencies = await get_available_currencies()
        
        # Fallback currencies if API is not available
        if not currencies:
            logger.warning("NOWPayments API not available, using fallback currencies")
            currencies = ['BTC', 'ETH', 'USDT', 'USDC', 'LTC', 'DOGE', 'BNBBSC', 'ADA', 'XRP', 'SOL', 'DOT', 'MATIC']
        
        # Debug: Log available currencies
        logger.info(f"Available currencies: {currencies}")
        
        # Handle the merchant coins response format
        if isinstance(currencies, list):
            # Convert currency codes to lowercase for consistency
            available_currencies = [currency.lower() for currency in currencies]
        else:
            # Fallback to popular currencies if API response is unexpected
            available_currencies = ['btc', 'eth', 'usdt', 'usdc', 'ltc', 'doge', 'bnbbsc', 'ada', 'xrp', 'sol', 'dot', 'matic']
        
        # Create keyboard with available currencies
        keyboard = []
        row = []
        
        # Add all available currencies to the keyboard
        for currency in available_currencies:
            row.append(InlineKeyboardButton(
                currency.upper(), 
                callback_data=f"currency_{currency}"
            ))
            if len(row) == 3:
                keyboard.append(row)
                row = []
        
        # Add any remaining currencies in the last row
        if row:
            keyboard.append(row)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"💱 Select Payment Currency 💱\n\n"
            f"Amount: ${amount:.2f}\n\n"
            f"Choose your preferred cryptocurrency:",
            reply_markup=reply_markup
        )
        return CHOOSING_CURRENCY
        
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number!")
        return CHOOSING_AMOUNT

async def currency_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle currency selection and create payment following NOWPayments official flow"""
    query = update.callback_query
    await query.answer()
    
    currency = query.data.replace('currency_', '')
    amount = context.user_data.get('deposit_amount')
    
    if not amount:
        await query.edit_message_text("❌ Error: Amount not found. Please start over with /deposit")
        return ConversationHandler.END
    
    await query.edit_message_text("⏳ Creating payment... Please wait.")
    
    # Get Django user first
    user = await save_user(query.from_user)
    
    # Ensure user has NOWPayments sub-partner account
    await ensure_sub_partner_account(user)
    
    # Create payment following NOWPayments official flow
    payment, payment_data, error_message = await create_payment(user, amount, currency)
    
    if not payment:
        error_msg = error_message or "Failed to create payment. Please try again later."
        await query.edit_message_text(f"❌ {error_msg}")
        return ConversationHandler.END
    
    # Generate QR code
    processor = PaymentProcessor()
    payment_info = processor.get_payment_info(payment)
    
    # Create payment message with enhanced information
    payment_message = f"""
💳 Payment Created Successfully! 💳

💰 Amount: ${payment.amount_usd:.2f}
🪙 Crypto Amount: {payment.crypto_amount:.8f} {payment.currency.upper()}
📅 Expires: {payment.expires_at.strftime('%Y-%m-%d %H:%M')}

📍 Payment Address:
`{payment.payment_address}`

⚠️ Important:
• Send exactly {payment.crypto_amount:.8f} {payment.currency.upper()}
• Payment expires in 24 hours
• Funds will be added to your wallet after confirmation

Use /payments to check payment status.
    """
    
    await query.edit_message_text(payment_message, parse_mode='Markdown')
    
    # Send QR code if available
    if payment_info['qr_code']:
        try:
            qr_image = base64.b64decode(payment_info['qr_code'])
            await context.bot.send_photo(
                chat_id=query.from_user.id,
                photo=io.BytesIO(qr_image),
                caption="📱 Scan this QR code to pay"
            )
        except Exception as e:
            logger.error(f"Error sending QR code: {e}")
    
    return ConversationHandler.END

async def payments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's payment history"""
    user = await save_user(update.effective_user)
    payments = await get_user_payments(user)
    
    if not payments:
        await update.message.reply_text("No payment history found. Use /deposit to make your first payment!")
        return
    
    message = "📊 Payment History 📊\n\n"
    
    for payment in payments[:5]:  # Show last 5 payments
        status_emoji = {
            'PENDING': '⏳',
            'CONFIRMING': '🔄',
            'CONFIRMED': '✅',
            'FINISHED': '✅',
            'FAILED': '❌',
            'EXPIRED': '⏰',
            'REFUNDED': '↩️'
        }.get(payment.status, '❓')
        
        message += f"""
{status_emoji} Payment {payment.payment_id}
💰 Amount: ${payment.amount_usd}
🪙 Crypto: {payment.crypto_amount:.8f} {payment.currency.upper()}
📊 Status: {payment.get_status_display()}
📅 Date: {payment.created_at.strftime('%Y-%m-%d %H:%M')}
        """
    
    if len(payments) > 5:
        message += f"\n... and {len(payments) - 5} more payments"
    
    await update.message.reply_text(message)

async def transactions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await save_user(update.effective_user)
    transactions = await get_user_transactions(user)
    
    if not transactions:
        await update.message.reply_text("No transactions found.")
        return
    
    message = "📊 Transaction History 📊\n\n"
    
    for transaction in transactions:
        emoji = "💰" if transaction.amount > 0 else "💸"
        message += f"""
{emoji} {transaction.get_transaction_type_display()}
Amount: ${transaction.amount}
Balance After: ${transaction.balance_after}
Date: {transaction.created_at.strftime('%Y-%m-%d %H:%M')}
        """
    
    await update.message.reply_text(message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_message = """
🚀 CryptoPayment Bot Help 🚀

Available Commands:
/start - Welcome message and introduction
/balance - Check your wallet balance
/deposit - Add funds to your wallet (cryptocurrency)
/transactions - View transaction history
/payments - View payment history
/status - Check recent payment status
/help - Show this help message

How to use:
1. Check your balance with /balance
2. Add funds with /deposit (cryptocurrency)
3. Monitor your transactions with /transactions
4. Check payment status with /payments or /status

Supported cryptocurrencies: BTC, ETH, USDT, USDC, LTC, DOGE, and more!

🔒 Secure and reliable cryptocurrency payments!
    """
    
    await update.message.reply_text(help_message)

async def check_payment_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check payment status manually (Step 8 of NOWPayments flow)"""
    user = await save_user(update.effective_user)
    
    # Get user's recent payments
    payments = await get_user_payments(user)
    
    if not payments:
        await update.message.reply_text("No payments found. Use /deposit to make your first payment!")
        return
    
    # Show last 3 payments with status
    message = "📊 Recent Payment Status 📊\n\n"
    
    for payment in payments[:3]:
        status_emoji = {
            'PENDING': '⏳',
            'CONFIRMING': '🔄',
            'CONFIRMED': '✅',
            'FINISHED': '✅',
            'FAILED': '❌',
            'EXPIRED': '⏰',
            'REFUNDED': '↩️'
        }.get(payment.status, '❓')
        
        message += f"""
{status_emoji} Payment {str(payment.payment_id)[:8]}...
💰 Amount: ${payment.amount_usd}
🪙 Crypto: {payment.crypto_amount:.8f} {payment.currency.upper() if payment.crypto_amount else 'N/A'}
📊 Status: {payment.get_status_display()}
📅 Date: {payment.created_at.strftime('%Y-%m-%d %H:%M')}
        """
    
    await update.message.reply_text(message)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the conversation"""
    await update.message.reply_text("❌ Operation cancelled.")
    return ConversationHandler.END

def main() -> None:
    """Start the bot."""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not found in environment variables")
        return
    
    try:
        # Create the Application and pass it your bot's token.
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Create conversation handler for deposit flow
        deposit_handler = ConversationHandler(
            entry_points=[CommandHandler("deposit", deposit)],
            states={
                CHOOSING_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, amount_received)],
                CHOOSING_CURRENCY: [CallbackQueryHandler(currency_selected, pattern="^currency_")]
            },
            fallbacks=[CommandHandler("cancel", cancel)]
        )
        
        # Add command handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("balance", balance))
        application.add_handler(deposit_handler)
        application.add_handler(CommandHandler("payments", payments))
        application.add_handler(CommandHandler("transactions", transactions))
        application.add_handler(CommandHandler("status", check_payment_status))
        application.add_handler(CommandHandler("help", help_command))

        logger.info("CryptoPayment bot started successfully")
        # Run the bot until the user presses Ctrl-C
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise

if __name__ == "__main__":
    main()