from django.db import models
from django.core.exceptions import ValidationError
from users.models import User
from datetime import date, timedelta
import decimal

class LoanApplication(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    REASON_CHOICES = (
        ('tuition', 'Tuition Fees'),
        ('books', 'Books and Materials'),
        ('living', 'Living Expenses'),
        ('other', 'Other Education Expenses'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loan_applications')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    reason_details = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Loan Application #{self.id} - {self.user.email}"
    
    def clean(self):
        # Add validation to ensure amount is positive
        if self.amount <= 0:
            raise ValidationError("Loan amount must be greater than zero")

class Loan(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('paid', 'Paid'),
        ('defaulted', 'Defaulted'),
    )
    
    application = models.OneToOneField(LoanApplication, on_delete=models.CASCADE, related_name='loan')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loans')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)  # Annual interest rate in percentage
    term_months = models.PositiveIntegerField()  # Loan term in months
    monthly_payment = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    disbursed_date = models.DateField()
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Loan #{self.id} - {self.user.email}"
    
    def clean(self):
        # Add validation logic
        if self.amount <= 0:
            raise ValidationError("Loan amount must be greater than zero")
        if self.interest_rate < 0:
            raise ValidationError("Interest rate cannot be negative")
        if self.term_months <= 0:
            raise ValidationError("Loan term must be at least one month")
        if self.disbursed_date > self.due_date:
            raise ValidationError("Due date must be after disbursement date")
    
    @classmethod
    def create_from_application(cls, application, interest_rate, term_months, disbursed_date=None):
        """
        Create a loan from an approved application with calculated terms
        """
        if application.status != 'approved':
            raise ValidationError("Can only create loan from approved applications")
        
        if disbursed_date is None:
            disbursed_date = date.today()
        
        # Calculate monthly payment using amortization formula
        # M = P * (r * (1 + r)^n) / ((1 + r)^n - 1)
        # where M = monthly payment, P = principal, r = monthly interest rate, n = number of payments
        
        principal = application.amount
        annual_rate = decimal.Decimal(interest_rate) / 100
        monthly_rate = annual_rate / 12
        num_payments = term_months
        
        # Avoid division by zero for 0% interest loans
        if monthly_rate == 0:
            monthly_payment = principal / num_payments
        else:
            monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)
            monthly_payment = round(monthly_payment, 2)
        
        # Calculate due date
        due_date = disbursed_date + timedelta(days=30 * term_months)
        
        # Create the loan
        loan = cls(
            application=application,
            user=application.user,
            amount=principal,
            interest_rate=interest_rate,
            term_months=term_months,
            monthly_payment=monthly_payment,
            disbursed_date=disbursed_date,
            due_date=due_date
        )
        
        return loan
    
    def calculate_remaining_balance(self):
        """
        Calculate the remaining balance on the loan
        """
        # Get total paid amount from repayments
        total_paid = sum(
            repayment.amount for repayment in self.repayments.filter(status='paid')
        )
        
        # Calculate remaining balance
        remaining = self.amount - total_paid
        
        # Ensure we don't return negative amounts if overpaid
        return max(decimal.Decimal('0.00'), remaining)
    
    def is_due_for_repayment(self):
        """
        Check if loan is due for repayment (has pending repayments)
        """
        return self.repayments.filter(status='pending').exists()
    
    def get_next_repayment(self):
        """
        Get the next pending repayment
        """
        pending_repayments = self.repayments.filter(status='pending').order_by('due_date')
        return pending_repayments.first()

class Repayment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('late', 'Late'),
        ('missed', 'Missed'),
    )
    
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='repayments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='repayments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    payment_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Repayment #{self.id} for Loan #{self.loan.id}"
    
    def clean(self):
        if self.amount <= 0:
            raise ValidationError("Repayment amount must be greater than zero")
    
    @classmethod
    def generate_repayment_schedule(cls, loan):
        """
        Generate a repayment schedule for a loan
        """
        # Clear any existing repayments that are still pending
        loan.repayments.filter(status='pending').delete()
        
        # Generate new repayment schedule
        current_date = loan.disbursed_date
        monthly_payment = loan.monthly_payment
        
        repayments = []
        for i in range(loan.term_months):
            # Calculate next due date (approximately one month later)
            next_date = date(
                year=current_date.year + ((current_date.month + 1) // 12),
                month=((current_date.month + 1) % 12) or 12,  # handle December
                day=min(current_date.day, 28)  # avoid issues with month lengths
            )
            
            # Create repayment object
            repayment = cls(
                loan=loan,
                user=loan.user,
                amount=monthly_payment,
                due_date=next_date,
                status='pending'
            )
            repayments.append(repayment)
            
            # Update current date for next iteration
            current_date = next_date
        
        # Adjust final payment to account for rounding errors
        remaining_balance = loan.amount - (monthly_payment * (loan.term_months - 1))
        if repayments:
            repayments[-1].amount = max(decimal.Decimal('0.01'), remaining_balance)
        
        # Save all repayments
        for repayment in repayments:
            repayment.save()
        
        return repayments 