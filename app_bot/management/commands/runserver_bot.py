import subprocess
import time
import os
import sys
import signal
from django.core.management.base import BaseCommand
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Run both Django server and Telegram bot simultaneously'

    def add_arguments(self, parser):
        parser.add_argument(
            '--port',
            type=int,
            default=8000,
            help='Port to run Django server on (default: 8000)'
        )
        parser.add_argument(
            '--host',
            type=str,
            default='127.0.0.1',
            help='Host to run Django server on (default: 127.0.0.1)'
        )

    def handle(self, *args, **options):
        host = options['host']
        port = options['port']

        self.stdout.write(
            self.style.SUCCESS('Starting Django server and Telegram bot...')
        )

        # Start the bot in a separate process
        bot_process = subprocess.Popen([
            sys.executable, 'manage.py', 'runbot'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Give the bot a moment to start
        time.sleep(3)

        # Start the Django server in the main process
        try:
            server_process = subprocess.Popen([
                sys.executable, 'manage.py', 'runserver', f'{host}:{port}'
            ])

            self.stdout.write(
                self.style.SUCCESS(f'Both services started. Django server on {host}:{port}')
            )

            # Wait for the server process to finish
            server_process.wait()
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('Shutting down...')
            )
        finally:
            # Clean up bot process
            if bot_process.poll() is None:
                bot_process.terminate()
                bot_process.wait() 