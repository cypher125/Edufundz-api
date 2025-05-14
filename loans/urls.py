from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'applications', views.LoanApplicationViewSet, basename='loan-application')
router.register(r'loans', views.LoanViewSet, basename='loan')
router.register(r'repayments', views.RepaymentViewSet, basename='repayment')

urlpatterns = [
    path('', include(router.urls)),
] 