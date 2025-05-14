from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'wallet', views.WalletViewSet, basename='wallet')
router.register(r'transactions', views.TransactionViewSet, basename='transaction')
router.register(r'virtual-accounts', views.VirtualAccountViewSet, basename='virtual-account')

urlpatterns = [
    path('', include(router.urls)),
    path('verify-payment/<str:reference>/', views.verify_payment, name='verify-payment'),
] 