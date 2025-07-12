from django.db import models
from app_account.models import User
import uuid
from decimal import Decimal


class Wallet(models.Model):
    """User wallet for managing funds"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.telegram_full_name}'s Wallet - ${self.balance}"

    def can_afford(self, amount):
        """Check if wallet has sufficient balance"""
        return self.balance >= amount

    def add_funds(self, amount, transaction_type="DEPOSIT"):
        """Add funds to wallet and create transaction record"""
        self.balance += amount
        self.save()
        Transaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type=transaction_type,
            balance_after=self.balance
        )

    def deduct_funds(self, amount, transaction_type="PURCHASE"):
        """Deduct funds from wallet and create transaction record"""
        if self.can_afford(amount):
            self.balance -= amount
            self.save()
            Transaction.objects.create(
                wallet=self,
                amount=-amount,
                transaction_type=transaction_type,
                balance_after=self.balance
            )
            return True
        return False


class Payment(models.Model):
    """Payment records for NOWPayments integration"""
    PAYMENT_STATUS = [
        ('PENDING', 'Pending'),
        ('CONFIRMING', 'Confirming'),
        ('CONFIRMED', 'Confirmed'),
        ('SENDING', 'Sending'),
        ('PARTIALLY_PAID', 'Partially Paid'),
        ('FINISHED', 'Finished'),
        ('FAILED', 'Failed'),
        ('EXPIRED', 'Expired'),
        ('REFUNDED', 'Refunded'),
    ]

    payment_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    amount_usd = models.DecimalField(max_digits=10, decimal_places=2)
    crypto_amount = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    currency = models.CharField(max_length=10)  # BTC, ETH, etc.
    nowpayments_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    payment_address = models.CharField(max_length=255, null=True, blank=True)
    payment_extra_id = models.CharField(max_length=255, null=True, blank=True)  # For XRP, XMR, etc.
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_processed = models.BooleanField(default=False)

    def __str__(self):
        return f"Payment {self.payment_id} - {self.user.telegram_full_name} - ${self.amount_usd}"

    class Meta:
        ordering = ['-created_at']


class Transaction(models.Model):
    """Wallet transaction history"""
    TRANSACTION_TYPES = [
        ('DEPOSIT', 'Deposit'),
        ('PURCHASE', 'Purchase'),
        ('WINNING', 'Winnings'),
        ('REFUND', 'Refund'),
        ('WITHDRAWAL', 'Withdrawal'),
    ]

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.TextField(blank=True)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.wallet.user.telegram_full_name} - {self.get_transaction_type_display()} - ${self.amount}"

    class Meta:
        ordering = ['-created_at']
