from django.shortcuts import render
from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from .models import Wallet, Transaction, VirtualAccount
from .serializers import WalletSerializer, TransactionSerializer, PaymentInitializeSerializer, VirtualAccountSerializer
from .paystack import initialize_transaction, verify_transaction, create_dedicated_account
import uuid

# Create your views here.

class WalletViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Wallet.objects.filter(user=self.request.user)
    
    def list(self, request, *args, **kwargs):
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(wallet)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def deposit(self, request):
        """Initiate a deposit to wallet using Paystack"""
        serializer = PaymentInitializeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        amount = serializer.validated_data['amount']
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        
        # Generate a unique reference
        reference = str(uuid.uuid4())
        
        # Create a pending transaction
        transaction = Transaction.objects.create(
            wallet=wallet,
            amount=amount,
            transaction_type='deposit',
            reference=reference,
            status='pending',
            description=f"Deposit of {amount} to wallet"
        )
        
        # Initialize payment with Paystack
        result = initialize_transaction(
            email=request.user.email,
            amount=float(amount)
        )
        
        if result['status']:
            # Update transaction with Paystack reference
            transaction.paystack_reference = result['reference']
            transaction.save()
            
            # Return the payment URL
            return Response({
                'status': 'success',
                'transaction_id': transaction.id,
                'reference': transaction.reference,
                'payment_url': result['authorization_url']
            })
        else:
            # Update transaction status to failed
            transaction.status = 'failed'
            transaction.save()
            
            return Response({
                'status': 'error',
                'message': result['message']
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get', 'post'])
    def virtual_account(self, request):
        """Get or create a virtual account for the user"""
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        
        # Try to get existing virtual account
        try:
            virtual_account = VirtualAccount.objects.get(user=request.user)
            if request.method == 'GET':
                serializer = VirtualAccountSerializer(virtual_account)
                return Response(serializer.data)
        except VirtualAccount.DoesNotExist:
            if request.method == 'GET':
                return Response({
                    'status': 'error',
                    'message': 'Virtual account not created yet'
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Create virtual account if POST request
        if request.method == 'POST':
            # If already exists, return it
            if 'virtual_account' in locals():
                return Response({
                    'status': 'success',
                    'message': 'Virtual account already exists',
                    'virtual_account': VirtualAccountSerializer(virtual_account).data
                })
            
            # Create a virtual account with Paystack
            result = create_dedicated_account(
                customer_email=request.user.email,
                first_name=request.user.first_name,
                last_name=request.user.last_name,
                phone=request.user.phone_number
            )
            
            if result['status']:
                # Create virtual account record
                virtual_account = VirtualAccount.objects.create(
                    wallet=wallet,
                    user=request.user,
                    account_number=result['account_number'],
                    account_name=result['account_name'],
                    bank_name=result['bank_name'],
                    status='active',
                    paystack_reference=result['data']['dedicated_account_number']
                )
                
                return Response({
                    'status': 'success',
                    'message': 'Virtual account created successfully',
                    'virtual_account': VirtualAccountSerializer(virtual_account).data
                })
            else:
                return Response({
                    'status': 'error',
                    'message': result['message']
                }, status=status.HTTP_400_BAD_REQUEST)

class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        wallet = Wallet.objects.get(user=self.request.user)
        return Transaction.objects.filter(wallet=wallet)

class VirtualAccountViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = VirtualAccountSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return VirtualAccount.objects.filter(user=self.request.user)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verify_payment(request, reference):
    """Verify a payment using Paystack"""
    try:
        transaction = Transaction.objects.get(reference=reference)
        
        # Only verify pending transactions
        if transaction.status != 'pending':
            return Response({
                'status': 'error',
                'message': f"Transaction is already {transaction.status}"
            })
        
        # Verify with Paystack
        result = verify_transaction(transaction.paystack_reference)
        
        if result['status']:
            paystack_data = result['data']
            
            if paystack_data['status'] == 'success':
                # Update transaction status
                transaction.status = 'completed'
                transaction.save()
                
                # Update wallet balance
                wallet = transaction.wallet
                wallet.balance += transaction.amount
                wallet.save()
                
                return Response({
                    'status': 'success',
                    'message': 'Payment verified successfully',
                    'transaction': TransactionSerializer(transaction).data,
                    'wallet_balance': wallet.balance
                })
            else:
                return Response({
                    'status': 'error',
                    'message': f"Payment verification failed: {paystack_data['gateway_response']}"
                })
        else:
            return Response({
                'status': 'error',
                'message': result['message']
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Transaction.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Transaction not found'
        }, status=status.HTTP_404_NOT_FOUND)
