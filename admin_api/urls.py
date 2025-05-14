from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserAdminViewSet, 
    LoanAdminViewSet, 
    LoanApplicationAdminViewSet,
    RepaymentAdminViewSet,
    WalletAdminViewSet,
    TransactionAdminViewSet,
    VirtualAccountAdminViewSet,
    dashboard_stats,
    admin_login,
    refresh_token,
    test_auth
)

router = DefaultRouter()
router.register(r'users', UserAdminViewSet)
router.register(r'loans', LoanAdminViewSet)
router.register(r'loan-applications', LoanApplicationAdminViewSet)
router.register(r'repayments', RepaymentAdminViewSet)
router.register(r'wallets', WalletAdminViewSet)
router.register(r'transactions', TransactionAdminViewSet)
router.register(r'virtual-accounts', VirtualAccountAdminViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/stats/', dashboard_stats, name='dashboard-stats'),
    path('login/', admin_login, name='admin-login'),
    path('refresh-token/', refresh_token, name='refresh-token'),
    path('test-auth/', test_auth, name='test-auth'),
] 