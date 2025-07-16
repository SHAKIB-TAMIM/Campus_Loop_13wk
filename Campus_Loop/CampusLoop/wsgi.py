import sys
import os

# Correct path to the outer folder that contains manage.py
path = '/home/ShakibTamim/Campus_Loop_13wk'
if path not in sys.path:
    sys.path.insert(0, path)

# This must match your actual Django project directory
os.environ['DJANGO_SETTINGS_MODULE'] = 'Campus_Loop.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
