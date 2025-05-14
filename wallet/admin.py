from django.contrib import admin
from .models import Wallet, Transaction, VirtualAccount

class WalletAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'balance', 'created_at', 'updated_at')
    search_fields = ('user__email', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 20

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'wallet', 'amount', 'transaction_type', 'status', 'reference', 'created_at')
    list_filter = ('transaction_type', 'status', 'created_at')
    search_fields = ('wallet__user__email', 'wallet__user__username', 'reference', 'paystack_reference')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 20

class VirtualAccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'account_number', 'account_name', 'bank_name', 'status', 'created_at')
    list_filter = ('status', 'bank_name', 'created_at')
    search_fields = ('user__email', 'user__username', 'account_number', 'account_name')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 20

# Register the models
admin.site.register(Wallet, WalletAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(VirtualAccount, VirtualAccountAdmin)
