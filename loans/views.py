from rest_framework import viewsets, status, generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from .models import LoanApplication, Loan, Repayment
from .serializers import LoanApplicationSerializer, LoanSerializer, RepaymentSerializer
from datetime import date

class LoanApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = LoanApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return LoanApplication.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        # Save with pending status and don't auto-create a loan
        serializer.save(user=self.request.user, status='pending')
        
        # Log the application creation
        loan_app = serializer.instance
        print(f"[INFO] New loan application created: ID #{loan_app.id}, Amount: {loan_app.amount}, Status: {loan_app.status}")
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Admin action to approve a loan application
        """
        application = self.get_object()
        
        if application.status != 'pending':
            return Response(
                {'detail': 'Only pending applications can be approved'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get loan terms from request data
        interest_rate = request.data.get('interest_rate', 5.0)
        term_months = request.data.get('term_months', 12)
        
        try:
            # Update application status
            application.status = 'approved'
            application.save()
            
            # Create a loan from the application
            loan = Loan.create_from_application(
                application=application,
                interest_rate=interest_rate,
                term_months=term_months,
                disbursed_date=date.today()
            )
            loan.save()
            
            # Generate repayment schedule
            Repayment.generate_repayment_schedule(loan)
            
            # Return updated application with loan details
            serializer = self.get_serializer(application)
            return Response(serializer.data)
        except Exception as e:
            # Revert application status if loan creation fails
            application.status = 'pending'
            application.save()
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Admin action to reject a loan application
        """
        application = self.get_object()
        
        if application.status != 'pending':
            return Response(
                {'detail': 'Only pending applications can be rejected'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update application status
        application.status = 'rejected'
        application.save()
        
        # Return updated application
        serializer = self.get_serializer(application)
        return Response(serializer.data)

class LoanViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LoanSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Loan.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['get'])
    def schedule(self, request, pk=None):
        """
        Get the repayment schedule for a loan
        """
        loan = self.get_object()
        repayments = loan.repayments.all().order_by('due_date')
        serializer = RepaymentSerializer(repayments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def remaining_balance(self, request, pk=None):
        """
        Get the remaining balance on a loan
        """
        loan = self.get_object()
        return Response({
            'loan_id': loan.id,
            'remaining_balance': loan.calculate_remaining_balance(),
            'is_paid': loan.status == 'paid'
        })

class RepaymentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RepaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Repayment.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        """
        Mark a repayment as paid (linked with wallet transaction)
        """
        repayment = self.get_object()
        
        if repayment.status == 'paid':
            return Response({'detail': 'Repayment already paid'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Logic to handle the payment will be added here
        # This would typically involve:
        # 1. Checking wallet balance
        # 2. Creating a transaction
        # 3. Updating the repayment status
        
        return Response({'detail': 'Payment endpoint needs to be linked with wallet transactions'}, 
                        status=status.HTTP_501_NOT_IMPLEMENTED) 