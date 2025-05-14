from rest_framework import serializers
from .models import Wallet, Transaction, VirtualAccount

class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['id', 'user', 'balance', 'created_at', 'updated_at']
        read_only_fields = ['user', 'balance', 'created_at', 'updated_at']

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            'id', 'wallet', 'amount', 'transaction_type', 
            'reference', 'paystack_reference', 'status', 
            'description', 'created_at', 'updated_at'
        ]
        read_only_fields = ['wallet', 'reference', 'paystack_reference', 'status', 'created_at', 'updated_at']

class VirtualAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = VirtualAccount
        fields = [
            'id', 'wallet', 'user', 'account_number', 'account_name',
            'bank_name', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['wallet', 'user', 'account_number', 'account_name',
                           'bank_name', 'status', 'created_at', 'updated_at']

class PaymentInitializeSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        return value 