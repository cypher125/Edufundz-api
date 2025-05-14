from django.contrib import admin
# Importing models for reference but not registering them again
from users.models import User
from loans.models import Loan, LoanApplication, Repayment
from wallet.models import Wallet, Transaction, VirtualAccount

# These models are already registered in their respective app's admin.py files
# Admin models defined here are just for reference and should not be registered again

# Note: If you want to customize how these models appear in the Django admin,
# modify the admin.py file in each app instead of here 