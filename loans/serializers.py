from rest_framework import serializers
from .models import LoanApplication, Loan, Repayment

class LoanApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanApplication
        fields = ['id', 'user', 'amount', 'reason', 'reason_details', 'status', 'created_at', 'updated_at']
        read_only_fields = ['user', 'status', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        # Automatically set the user from the request
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)

class LoanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = [
            'id', 'application', 'user', 'amount', 'interest_rate', 'term_months', 
            'monthly_payment', 'status', 'disbursed_date', 'due_date', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']

class RepaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Repayment
        fields = [
            'id', 'loan', 'user', 'amount', 'due_date', 'payment_date', 
            'status', 'transaction_id', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at'] 