from django.core.management.base import BaseCommand
from django.db import transaction
import sys
import os

class Command(BaseCommand):
    help = 'Populates the database with example data for the teacher dashboard'

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                # Import and run the populate_data script
                sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
                from populate_data import run
                run()
                
            self.stdout.write(self.style.SUCCESS('Successfully populated database with example data'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error populating database: {str(e)}'))
