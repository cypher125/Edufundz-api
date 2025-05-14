import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edufundz.settings')
django.setup()

from users.models import User
from django.db import transaction

def create_superuser():
    # Check if a superuser already exists
    if User.objects.filter(is_superuser=True).exists():
        print("A superuser already exists.")
        return

    try:
        with transaction.atomic():
            # Create superuser
            superuser = User.objects.create_superuser(
                username="admin",
                email="admin@edufundz.com",
                password="adminpassword123",
                first_name="Admin",
                last_name="User"
            )
            print(f"Superuser created successfully: {superuser.email}")
    except Exception as e:
        print(f"Error creating superuser: {e}")

if __name__ == "__main__":
    create_superuser() 