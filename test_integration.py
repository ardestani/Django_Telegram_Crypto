#!/usr/bin/env python
"""
Test script to verify Django and Telegram bot integration
"""
import os
import sys
import django
from dotenv import load_dotenv
import traceback
import random
import string

# Load environment variables
load_dotenv()

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lottolite.settings')
django.setup()

def test_django_models():
    """Test that Django models can be accessed"""
    try:
        from app_account.models import User
        print("✓ Django models imported successfully")
        # Generate a random username to avoid UNIQUE constraint errors
        rand_username = "test_user_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        user, created = User.objects.get_or_create(
            username=rand_username,
            telegram_username=rand_username,
            telegram_full_name="Test User",
            telegram_id=rand_username,
            defaults={'is_active': True, 'is_admin': False}
        )
        print(f"✓ User {'created' if created else 'retrieved'} successfully: {user.telegram_full_name}")
        return True
    except Exception as e:
        print(f"✗ Django models test failed: {e}")
        traceback.print_exc()
        return False

def test_bot_import():
    """Test that bot can be imported"""
    try:
        from app_bot.bot import main, save_user, start
        print("✓ Bot functions imported successfully")
        return True
    except Exception as e:
        print(f"✗ Bot import test failed: {e}")
        return False

def test_management_commands():
    """Test that management commands can be imported"""
    try:
        from app_bot.management.commands.runbot import Command as RunBotCommand
        from app_bot.management.commands.runserver_bot import Command as RunServerBotCommand
        print("✓ Management commands imported successfully")
        return True
    except Exception as e:
        print(f"✗ Management commands test failed: {e}")
        return False

def test_environment():
    """Test environment variables"""
    bot_token = os.getenv('BOT_TOKEN')
    if bot_token:
        print(f"✓ BOT_TOKEN found: {bot_token[:10]}...")
        return True
    else:
        print("✗ BOT_TOKEN not found in environment")
        return False

def main():
    print("Testing Django and Telegram Bot Integration")
    print("=" * 50)
    
    tests = [
        ("Environment Variables", test_environment),
        ("Django Models", test_django_models),
        ("Bot Import", test_bot_import),
        ("Management Commands", test_management_commands),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        if test_func():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed! Integration is working correctly.")
        print("\nYou can now use:")
        print("  python manage.py runserver     # Django server only")
        print("  python manage.py runbot        # Bot only")
        print("  python manage.py runserver_bot # Both together")
    else:
        print("✗ Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 