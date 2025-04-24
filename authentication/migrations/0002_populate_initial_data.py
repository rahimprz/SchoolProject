from django.db import migrations
import os
import sys
import django

def populate_data(apps, schema_editor):
    # Set the correct settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    
    # Import and run the populate_data script
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from populate_data import run
    run()

class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0001_initial'),  # Replace with your actual initial migration
    ]

    operations = [
        migrations.RunPython(populate_data),
    ]
