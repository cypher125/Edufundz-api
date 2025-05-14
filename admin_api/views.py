from rest_framework import viewsets, permissions, status, views
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from users.models import User
from loans.models import Loan, LoanApplication, Repayment
from wallet.models import Wallet, Transaction, VirtualAccount
from users.serializers import UserSerializer
from loans.serializers import LoanSerializer, LoanApplicationSerializer, RepaymentSerializer
from wallet.serializers import WalletSerializer, TransactionSerializer, VirtualAccountSerializer
from django.db.models import Sum
import jwt
from datetime import datetime, timedelta
import logging
from rest_framework.permissions import AllowAny

# Set up logger
logger = logging.getLogger(__name__)

class AdminPermission(permissions.BasePermission):
    """
    Custom permission to only allow admin users to access admin API
    """
    def has_permission(self, request, view):
        # Log the request details for debugging
        logger.info(f"AdminPermission check - Path: {request.path}, Method: {request.method}")
        logger.info(f"Headers: {request.META.get('HTTP_AUTHORIZATION', 'No Authorization header')}")
        
        # Check for Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        logger.info(f"Auth header: {auth_header}")
        
        if not auth_header:
            logger.warning("Missing Authorization header")
            return False
        
        # Support both Token and Bearer formats
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            logger.info("Using Bearer token format")
            try:
                # Decode token and verify
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('user_id')
                
                # Check if token is expired
                exp = payload.get('exp')
                if datetime.fromtimestamp(exp) < datetime.now():
                    logger.warning(f"Token expired for user {user_id}")
                    return False
                    
                # Get user and check if admin
                user = User.objects.get(id=user_id)
                if not user.is_staff and not user.is_superuser:
                    logger.warning(f"User {user.email} is not an admin")
                    return False
                    
                # Attach user to request
                request.user = user
                logger.info(f"Successfully authenticated admin user: {user.email}")
                return True
                
            except jwt.ExpiredSignatureError:
                logger.warning("Token signature expired")
                return False
            except jwt.InvalidTokenError:
                logger.warning("Invalid token")
                return False
            except User.DoesNotExist:
                logger.warning(f"User with ID {user_id} not found")
                return False
            except Exception as e:
                logger.error(f"Error validating token: {str(e)}")
                return False
        elif auth_header.startswith('Token '):
            # Support legacy token format for compatibility
            token_key = auth_header.split(' ')[1]
            logger.info("Using Token format")
            try:
                token = Token.objects.get(key=token_key)
                user = token.user
                if not user.is_staff and not user.is_superuser:
                    logger.warning(f"User {user.email} is not an admin (Token auth)")
                    return False
                    
                # Attach user to request
                request.user = user
                logger.info(f"Successfully authenticated admin user via Token: {user.email}")
                return True
            except Token.DoesNotExist:
                logger.warning("Invalid token key")
                return False
            except Exception as e:
                logger.error(f"Error validating token: {str(e)}")
                return False
        else:
            logger.warning(f"Unsupported authorization format: {auth_header[:15]}...")
            return False


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def admin_login(request):
    """
    Admin login endpoint with JWT token
    """
    try:
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            logger.warning("Missing email or password in admin login request")
            return Response(
                {'detail': 'Please provide both email and password.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logger.info(f"Admin login attempt for email: {email}")
        
        # Try to authenticate with email
        user = authenticate(request=request, email=email, password=password)
        
        # If that fails, try with username (which will be mapped to email by our custom backend)
        if user is None:
            user = authenticate(request=request, username=email, password=password)
        
        if user is None:
            logger.warning(f"Authentication failed for {email}")
            return Response(
                {'detail': 'Invalid credentials.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Check if user is staff
        if not user.is_staff and not user.is_superuser:
            logger.warning(f"User {email} is not staff/admin")
            return Response(
                {'detail': 'User is not authorized for admin access.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create JWT token with expiration (24 hours)
        expiration = datetime.now() + timedelta(hours=24)
        payload = {
            'user_id': user.id,
            'email': user.email,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'exp': expiration.timestamp()
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        
        # Also create refresh token (valid for 7 days)
        refresh_expiration = datetime.now() + timedelta(days=7)
        refresh_payload = {
            'user_id': user.id,
            'token_type': 'refresh',
            'exp': refresh_expiration.timestamp()
        }
        refresh_token = jwt.encode(refresh_payload, settings.SECRET_KEY, algorithm='HS256')
        
        logger.info(f"Admin login successful for {email}")
        
        # Return tokens and user data
        return Response({
            'access_token': token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': 24 * 3600,  # seconds
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser
            }
        })
    except Exception as e:
        logger.error(f"Unexpected error in admin login: {str(e)}")
        return Response(
            {'detail': 'An unexpected error occurred during login.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    """
    Endpoint to refresh an expired access token using a refresh token
    """
    refresh_token = request.data.get('refresh_token')
    if not refresh_token:
        return Response(
            {'detail': 'Refresh token is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Decode and verify the refresh token
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=['HS256'])
        
        # Check if it's a refresh token
        if payload.get('token_type') != 'refresh':
            logger.warning("Invalid token type")
            return Response(
                {'detail': 'Invalid token type.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_id = payload.get('user_id')
        user = User.objects.get(id=user_id)
        
        # Check if user is still admin
        if not user.is_staff and not user.is_superuser:
            logger.warning(f"User {user.email} is no longer admin")
            return Response(
                {'detail': 'User is not authorized for admin access.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create new access token
        expiration = datetime.now() + timedelta(hours=24)
        new_payload = {
            'user_id': user.id,
            'email': user.email,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'exp': expiration.timestamp()
        }
        new_token = jwt.encode(new_payload, settings.SECRET_KEY, algorithm='HS256')
        
        return Response({
            'access_token': new_token,
            'token_type': 'Bearer',
            'expires_in': 24 * 3600  # seconds
        })
        
    except jwt.ExpiredSignatureError:
        logger.warning("Refresh token expired")
        return Response(
            {'detail': 'Refresh token has expired.'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    except jwt.InvalidTokenError:
        logger.warning("Invalid refresh token")
        return Response(
            {'detail': 'Invalid refresh token.'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    except User.DoesNotExist:
        logger.warning(f"User with ID {user_id} not found")
        return Response(
            {'detail': 'User not found.'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        return Response(
            {'detail': 'Error refreshing token.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class UserAdminViewSet(viewsets.ModelViewSet):
    """
    API endpoint for admin to manage users
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AdminPermission]
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get user statistics"""
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        
        return Response({
            'total_users': total_users,
            'active_users': active_users,
        })


class LoanAdminViewSet(viewsets.ModelViewSet):
    """
    API endpoint for admin to manage loans
    """
    queryset = Loan.objects.all()
    serializer_class = LoanSerializer
    permission_classes = [AdminPermission]
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get loan statistics"""
        total_loans = Loan.objects.count()
        active_loans = Loan.objects.filter(status='active').count()
        paid_loans = Loan.objects.filter(status='paid').count()
        defaulted_loans = Loan.objects.filter(status='defaulted').count()
        
        return Response({
            'total_loans': total_loans,
            'active_loans': active_loans,
            'paid_loans': paid_loans,
            'defaulted_loans': defaulted_loans,
        })


class LoanApplicationAdminViewSet(viewsets.ModelViewSet):
    """
    API endpoint for admin to manage loan applications
    """
    queryset = LoanApplication.objects.all()
    serializer_class = LoanApplicationSerializer
    permission_classes = [AdminPermission]
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a loan application"""
        application = self.get_object()
        
        if application.status != 'pending':
            return Response(
                {'detail': 'Only pending applications can be approved'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update application status
        application.status = 'approved'
        application.save()
        
        # Return updated application
        serializer = self.get_serializer(application)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a loan application"""
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


class RepaymentAdminViewSet(viewsets.ModelViewSet):
    """
    API endpoint for admin to manage repayments
    """
    queryset = Repayment.objects.all()
    serializer_class = RepaymentSerializer
    permission_classes = [AdminPermission]


class WalletAdminViewSet(viewsets.ModelViewSet):
    """
    API endpoint for admin to manage wallets
    """
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer
    permission_classes = [AdminPermission]
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get wallet statistics"""
        total_wallets = Wallet.objects.count()
        total_balance = sum(wallet.balance for wallet in Wallet.objects.all())
        
        return Response({
            'total_wallets': total_wallets,
            'total_balance': total_balance,
        })


class TransactionAdminViewSet(viewsets.ModelViewSet):
    """
    API endpoint for admin to manage transactions
    """
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [AdminPermission]
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get transaction statistics"""
        total_transactions = Transaction.objects.count()
        total_deposits = Transaction.objects.filter(transaction_type='deposit').count()
        total_withdrawals = Transaction.objects.filter(transaction_type='withdrawal').count()
        
        return Response({
            'total_transactions': total_transactions,
            'total_deposits': total_deposits,
            'total_withdrawals': total_withdrawals,
        })


class VirtualAccountAdminViewSet(viewsets.ModelViewSet):
    """
    API endpoint for admin to manage virtual accounts
    """
    queryset = VirtualAccount.objects.all()
    serializer_class = VirtualAccountSerializer
    permission_classes = [AdminPermission] 


@api_view(['GET'])
@permission_classes([AdminPermission])
def dashboard_stats(request):
    """
    Aggregated statistics for the admin dashboard
    """
    # User stats
    total_users = User.objects.count()
    
    # Loan stats
    active_loans = Loan.objects.filter(status='active').count()
    total_loans = Loan.objects.count()
    paid_loans = Loan.objects.filter(status='paid').count()
    
    # Calculate loan amounts
    total_loan_amount = Loan.objects.filter(status='active').aggregate(
        Sum('amount')
    )['amount__sum'] or 0
    
    # Calculate repayment rate
    repayment_rate = 0
    if total_loans > 0:
        repayment_rate = (paid_loans / total_loans) * 100
        repayment_rate = round(repayment_rate, 1)  # Round to 1 decimal place
    
    return Response({
        'totalUsers': total_users,
        'activeLoans': active_loans,
        'totalLoanAmount': total_loan_amount,
        'repaymentRate': repayment_rate,
    })


@api_view(['GET'])
@permission_classes([AdminPermission])
def test_auth(request):
    """
    Simple endpoint to test if authentication is working correctly
    """
    logger.info(f"Test auth endpoint called by user: {request.user.email}")
    return Response({
        'success': True,
        'message': 'Authentication successful',
        'user': {
            'id': request.user.id,
            'email': request.user.email,
            'username': request.user.username,
            'is_staff': request.user.is_staff,
            'is_superuser': request.user.is_superuser
        }
    }) 