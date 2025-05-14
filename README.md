# EduFundz Backend

This is the backend API for the EduFundz application, built with Django and Django REST Framework.

## Features

- User authentication and registration
- Student loan application and management
- Wallet functionality for managing funds
- Paystack integration for payments and repayments
- Admin panel for loan approval and management

## Installation

1. Clone the repository:
```
git clone <repository-url>
cd edufundz/backend
```

2. Create a virtual environment and activate it:
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```
pip install -r requirements.txt
```

4. Run migrations:
```
python manage.py makemigrations
python manage.py migrate
```

5. Create a superuser:
```
python manage.py createsuperuser
```

6. Run the development server:
```
python manage.py runserver
```

The API will be available at http://localhost:8000/

## API Endpoints

### Authentication
- `POST /api/users/register/` - Register a new user
- `POST /api/users/login/` - Login and get auth token
- `POST /api/users/logout/` - Logout user
- `GET /api/users/profile/` - Get user profile

### Loans
- `GET /api/loans/applications/` - List loan applications
- `POST /api/loans/applications/` - Create new loan application
- `GET /api/loans/loans/` - List approved loans
- `GET /api/loans/repayments/` - List loan repayments
- `POST /api/loans/repayments/{id}/pay/` - Make payment for a repayment

### Wallet
- `GET /api/wallet/wallet/` - Get wallet details
- `POST /api/wallet/wallet/deposit/` - Initialize deposit to wallet
- `GET /api/wallet/transactions/` - List wallet transactions
- `GET /api/wallet/verify-payment/{reference}/` - Verify a payment

## Paystack Integration

This project uses Paystack for payment processing. To set up Paystack:

1. Create an account on [Paystack](https://paystack.com)
2. Get your test API keys from the Paystack dashboard
3. Replace the placeholder API keys in `settings.py`:
   ```python
   PAYSTACK_SECRET_KEY = 'your_secret_key'
   PAYSTACK_PUBLIC_KEY = 'your_public_key'
   ```

## Admin Interface

The Django admin interface is available at `/admin/`. You can use it to:
- Approve or reject loan applications
- Manage users
- View and manage transactions
- Monitor loan repayments

## Development

For development purposes, this project has CORS enabled for all origins. In production, you should restrict this to your frontend domain. 