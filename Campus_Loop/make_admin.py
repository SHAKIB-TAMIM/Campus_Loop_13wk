#!/usr/bin/env python
"""
Script to make a user admin in Campus Loop
Usage: python make_admin.py <email>
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CampusLoop.settings')
django.setup()

from django.contrib.auth.models import User

def make_user_admin(email):
    """Make a user admin by email"""
    try:
        user = User.objects.get(email=email)
        user.is_staff = True
        user.is_superuser = True
        user.save()
        print(f"✅ Success! User '{user.username}' ({email}) is now an admin.")
        print(f"   Full name: {user.get_full_name()}")
        print(f"   Username: {user.username}")
        print(f"   Staff status: {user.is_staff}")
        print(f"   Superuser status: {user.is_superuser}")
        print("\nYou can now log in with this email and will be redirected to the admin dashboard.")
    except User.DoesNotExist:
        print(f"❌ Error: No user found with email '{email}'")
        print("Please check the email address and try again.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python make_admin.py <email>")
        print("Example: python make_admin.py admin@example.com")
        sys.exit(1)
    
    email = sys.argv[1]
    make_user_admin(email) 