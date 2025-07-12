from django.contrib import admin
from .models import Wallet, Payment, Transaction


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__telegram_full_name', 'user__telegram_username']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_id', 'user', 'amount_usd', 'currency', 'status', 'created_at', 'is_processed']
    list_filter = ['status', 'currency', 'created_at', 'is_processed']
    search_fields = ['payment_id', 'user__telegram_full_name', 'user__telegram_username', 'nowpayments_id']
    readonly_fields = ['payment_id', 'created_at', 'updated_at', 'expires_at', 'crypto_amount_display']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'amount_usd', 'currency', 'status')
        }),
        ('NOWPayments Data', {
            'fields': ('nowpayments_id', 'payment_address', 'payment_extra_id', 'crypto_amount', 'crypto_amount_display')
        }),
        ('Processing', {
            'fields': ('is_processed', 'expires_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def crypto_amount_display(self, obj):
        """Display crypto amount rounded to 8 decimal places"""
        if obj.crypto_amount:
            return f"{float(obj.crypto_amount):.8f}"
        return "N/A"
    crypto_amount_display.short_description = "Crypto Amount (Rounded)"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['wallet', 'transaction_type', 'amount', 'balance_after', 'created_at']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['wallet__user__telegram_full_name', 'wallet__user__telegram_username']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('wallet__user')
