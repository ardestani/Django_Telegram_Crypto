# Django Telegram CryptoPayment

A comprehensive Django project template that integrates Telegram bots with cryptocurrency payments via NOWPayments, providing a solid foundation for building Telegram bot applications with crypto payment capabilities.

## Features

- **Django Integration**: Full Django project structure with models, views, and admin interface
- **Telegram Bot**: Ready-to-use Telegram bot with async/await support
- **Cryptocurrency Payments**: NOWPayments integration for crypto deposits and payments
- **User Management**: Django User model integration with Telegram users
- **Wallet System**: Digital wallet for managing funds
- **Payment Processing**: Complete payment flow with webhooks and verification
- **Management Commands**: Custom Django management commands for running bot and server
- **Environment Configuration**: Secure environment variable handling
- **Database Integration**: SQLite database with Django ORM
- **Admin Interface**: Django admin for managing all data
- **QR Code Generation**: Automatic QR code generation for payments
- **Webhook Integration**: Real-time payment status updates

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/Django_Telegram_CryptoPayment.git
cd Django_Telegram_CryptoPayment
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Setup
Create a `.env` file in the root directory:
```env
BOT_TOKEN=your_telegram_bot_token_here
BASE_URL=http://localhost:8000
SECRET_KEY=your_django_secret_key_here
DEBUG=True
NOWPAYMENTS_API_KEY=your_nowpayments_api_key_here
```

### 4. Database Setup
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

## Usage

### Run Django Server Only
```bash
python manage.py runserver
```

### Run Telegram Bot Only
```bash
python manage.py runbot
```

### Run Both Django Server and Telegram Bot Simultaneously
```bash
python manage.py runserver_bot
```

### Custom Host and Port
```bash
python manage.py runserver_bot --host 0.0.0.0 --port 8000
```

### Test NOWPayments Deposit Flow
Test the complete deposit flow implementation:
```bash
# Test with default values (amount=10.0, currency=btc)
python manage.py test_deposit_flow

# Test with custom values
python manage.py test_deposit_flow --amount 25.0 --currency eth

# Test with specific user
python manage.py test_deposit_flow --user-id 123456789 --amount 50.0 --currency usdt
```

## Bot Commands

- `/start` - Welcome message and introduction
- `/balance` - Check your wallet balance
- `/deposit` - Add funds to your wallet (cryptocurrency) - Complete NOWPayments flow
- `/payments` - View payment history
- `/transactions` - View transaction history
- `/status` - Check recent payment status manually
- `/help` - Show this help message

## Cryptocurrency Payment System

### NOWPayments Integration - Complete Deposit Flow
This template implements the complete NOWPayments deposit flow as per their official documentation:

1. **Registration and User Account Creation**: Users are automatically registered with NOWPayments sub-partner accounts
2. **UI - Deposit Amount & Currency Selection**: Bot asks for deposit amount and preferred cryptocurrency
3. **API - Minimum Payment Amount Validation**: Checks minimum required amount for the selected currency pair
4. **API - Estimated Price Calculation**: Gets estimated crypto amount and validates it meets minimum requirements
5. **API - Payment Creation**: Creates payment with NOWPayments and gets deposit address
6. **UI - Payment Instructions**: Bot provides payment address and QR code to user
7. **Payment Processing**: NOWPayments processes the payment and sends webhook notifications
8. **API - Payment Status Checking**: Manual status checking via `/status` command or webhooks
9. **API - Payments List**: Get list of all payments made to the account

### Payment Features
- **Complete Flow Validation**: Minimum amount and estimated price validation
- **Real-time Status Updates**: Via webhooks and manual status checking
- **QR Code Generation**: Automatic QR codes for easy mobile payments
- **Automatic Wallet Top-up**: Funds added after payment confirmation
- **Payment History Tracking**: Complete payment and transaction history
- **Multiple Cryptocurrency Support**: BTC, ETH, USDT, USDC, LTC, DOGE, and many more
- **Secure Payment Verification**: Server-side validation and processing
- **Sub-Partner Integration**: Each user gets their own NOWPayments sub-partner account

## Project Structure

```
Django_Telegram_CryptoPayment/
├── app_account/          # User management and authentication
│   ├── models.py         # User models
│   ├── views.py          # Account views
│   ├── admin.py          # Admin interface
│   └── migrations/       # Database migrations
├── app_bot/              # Telegram bot implementation
│   ├── bot.py            # Main bot logic with payment commands
│   ├── models.py         # Bot-specific models (Wallet, Payment, Transaction)
│   ├── services.py       # NOWPayments service integration
│   ├── views.py          # Bot web views and webhooks
│   ├── admin.py          # Bot admin interface
│   ├── urls.py           # URL patterns for webhooks
│   └── management/       # Custom management commands
│       └── commands/
│           ├── runbot.py
│           └── runserver_bot.py
├── templates/            # Django templates
│   ├── payment_success.html
│   └── payment_error.html
├── manage.py            # Django management script
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Configuration

### Django Settings
The main Django settings are in `lottolite/settings.py`. Key configurations:

- Database: SQLite by default (easily changeable to PostgreSQL/MySQL)
- Static files: Configured for development
- Templates: Set up for the template directory
- Installed apps: Includes both `app_account` and `app_bot`

### Bot Configuration
Bot settings are managed through environment variables:

- `BOT_TOKEN`: Your Telegram bot token from @BotFather
- `BASE_URL`: Base URL for webhook (if using webhooks)
- `DEBUG`: Django debug mode
- `NOWPAYMENTS_API_KEY`: Your NOWPayments API key

### NOWPayments Setup
1. Sign up at [NOWPayments](https://nowpayments.io/)
2. Get your API key from the dashboard
3. Add the API key to your `.env` file
4. Configure webhook URL in NOWPayments dashboard: `https://yourdomain.com/api/payment/webhook/`

## Models

### Core Models
- **User**: Extended Django user model with Telegram integration
- **Wallet**: User wallet for managing funds
- **Payment**: Payment records for NOWPayments integration
- **Transaction**: Wallet transaction history

### Payment Model Features
- Payment status tracking (Pending, Confirming, Confirmed, Finished, etc.)
- Cryptocurrency amount and address storage
- Expiration handling
- Webhook processing status

## Customization

### Adding New Bot Commands
1. Edit `app_bot/bot.py`
2. Add your command handlers
3. Register them in the bot setup

### Extending User Model
1. Modify `app_account/models.py`
2. Create and run migrations
3. Update bot logic in `app_bot/bot.py`

### Adding New Django Apps
1. Create new app: `python manage.py startapp your_app_name`
2. Add to `INSTALLED_APPS` in settings
3. Create models and views as needed

### Customizing Payment Flow
1. Modify `app_bot/services.py` for payment logic
2. Update `app_bot/bot.py` for bot commands
3. Customize templates in `templates/` directory

## Deployment

### Local Development
```bash
python manage.py runserver_bot
```

### Production Deployment
1. Set `DEBUG=False` in environment
2. Configure production database
3. Set up static file serving
4. Use a process manager like Supervisor or systemd
5. Configure webhook or polling for bot
6. Set up SSL for secure webhook endpoints

### Environment Variables for Production
```env
BOT_TOKEN=your_production_bot_token
BASE_URL=https://yourdomain.com
SECRET_KEY=your_production_secret_key
DEBUG=False
DATABASE_URL=your_database_url
NOWPAYMENTS_API_KEY=your_nowpayments_api_key
```

## Security Considerations

- All sensitive data is stored in environment variables
- Webhook endpoints are CSRF exempt but should be secured in production
- Payment verification is handled server-side
- User authentication is managed through Telegram
- Database transactions ensure data integrity
- API keys are never exposed in code

## API Endpoints

### Webhook Endpoint
- `POST /api/payment/webhook/` - NOWPayments webhook for payment updates

### Payment Status
- `GET /api/payment/status/<payment_id>/` - Get payment status by ID

### Payment Pages
- `GET /payment/success/<payment_id>/` - Payment success page
- `GET /payment/error/<payment_id>/` - Payment error page

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source and available under the [MIT License](LICENSE).

## Support

For issues and questions:
- Create an issue on GitHub
- Check the documentation
- Review the code examples

## Changelog

### Version 1.0.0
- Initial release
- Django 5.2.4+ support
- python-telegram-bot 20.0+ integration
- NOWPayments cryptocurrency integration
- Complete payment processing system
- Wallet management
- QR code generation
- Webhook integration
- Admin interface
- Environment-based configuration 