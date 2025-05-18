import os
from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import User


class Command(BaseCommand):
    help = 'Creates an admin user if no admin users exist'

    def handle(self, *args, **options):
        # Check if admin users already exist
        if User.objects.filter(role=User.ROLE_ADMIN).exists():
            self.stdout.write(self.style.SUCCESS('Admin user already exists. Skipping creation.'))
            return

        # Get admin credentials from environment variables or use defaults
        username = os.getenv('ADMIN_USERNAME', 'admin')
        email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
        password = os.getenv('ADMIN_PASSWORD', 'admin')
        first_name = os.getenv('ADMIN_FIRST_NAME', 'Admin')
        last_name = os.getenv('ADMIN_LAST_NAME', 'User')

        # Create admin user
        with transaction.atomic():
            admin_user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role=User.ROLE_ADMIN,
                is_staff=True,
                is_superuser=True
            )
            
        self.stdout.write(self.style.SUCCESS(
            f'Successfully created admin user: {admin_user.username} (role: {admin_user.role})')
        ) 