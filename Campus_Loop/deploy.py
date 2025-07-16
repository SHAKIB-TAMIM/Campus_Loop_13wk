#!/usr/bin/env python3
"""
Deployment helper script for Campus Loop
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def main():
    print("🚀 Campus Loop Deployment Helper")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not Path("manage.py").exists():
        print("❌ Error: manage.py not found. Please run this script from the project root.")
        sys.exit(1)
    
    # Step 1: Install dependencies
    if not run_command("pip install -r requirements.txt", "Installing dependencies"):
        sys.exit(1)
    
    # Step 2: Run migrations
    if not run_command("python manage.py migrate", "Running database migrations"):
        sys.exit(1)
    
    # Step 3: Collect static files
    if not run_command("python manage.py collectstatic --noinput", "Collecting static files"):
        sys.exit(1)
    
    # Step 4: Check if superuser exists
    print("🔍 Checking for superuser...")
    try:
        result = subprocess.run(
            "python manage.py shell -c \"from django.contrib.auth.models import User; print('Superuser exists' if User.objects.filter(is_superuser=True).exists() else 'No superuser found')\"",
            shell=True, capture_output=True, text=True
        )
        if "No superuser found" in result.stdout:
            print("⚠️  No superuser found. You may want to create one:")
            print("   python manage.py createsuperuser")
    except:
        pass
    
    print("\n✅ Deployment preparation completed!")
    print("\n📋 Next steps:")
    print("1. Set environment variables (DEBUG=False, SECRET_KEY)")
    print("2. Deploy to your chosen platform")
    print("3. Check the DEPLOYMENT.md file for detailed instructions")
    
    # Check if we're in production mode
    debug = os.environ.get('DEBUG', 'True').lower()
    if debug == 'true':
        print("\n⚠️  Warning: DEBUG is still True. Set DEBUG=False for production!")

if __name__ == "__main__":
    main() 