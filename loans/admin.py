from django.contrib import admin
from .models import Loan, LoanApplication, Repayment

class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'reason', 'status', 'created_at')
    list_filter = ('status', 'reason', 'created_at')
    search_fields = ('user__email', 'user__username', 'reason', 'reason_details')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 20

class LoanAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'status', 'interest_rate', 'term_months', 'disbursed_date', 'due_date')
    list_filter = ('status', 'disbursed_date', 'due_date')
    search_fields = ('user__email', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 20

class RepaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'loan', 'user', 'amount', 'due_date', 'payment_date', 'status')
    list_filter = ('status', 'due_date', 'payment_date')
    search_fields = ('user__email', 'user__username', 'loan__id')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 20

# Register the models
admin.site.register(LoanApplication, LoanApplicationAdmin)
admin.site.register(Loan, LoanAdmin)
admin.site.register(Repayment, RepaymentAdmin) 