import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'authentication.settings')
django.setup()

# Import and run the populate script
from populate_data import run
run()
