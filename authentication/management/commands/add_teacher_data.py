from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from authentication.models import Teacher

class Command(BaseCommand):
    help = 'Adds example teacher data to the database (without subjects or classrooms)'

    def handle(self, *args, **options):
        # Create teacher group if it doesn't exist
        teacher_group, created = Group.objects.get_or_create(name='Teacher')
        if created:
            self.stdout.write(self.style.SUCCESS('Created Teacher group'))
        
        # Create example teacher users
        teacher_data = [
            {
                'username': 'mthompson',
                'first_name': 'Michael',
                'last_name': 'Thompson',
                'email': 'mthompson@school.edu',
                'department': 'Mathematics',
                'years_experience': 8,
                'office': 'Room 305, Building B',
                'office_hours': 'Mon, Wed: 2:00 PM - 4:00 PM',
                'phone': '+44 7700 900123'
            },
            {
                'username': 'jjohnson',
                'first_name': 'Jennifer',
                'last_name': 'Johnson',
                'email': 'jjohnson@school.edu',
                'department': 'Science',
                'years_experience': 6,
                'office': 'Room 210, Building A',
                'office_hours': 'Tue, Thu: 1:00 PM - 3:00 PM',
                'phone': '+44 7700 900456'
            },
            {
                'username': 'dwilliams',
                'first_name': 'David',
                'last_name': 'Williams',
                'email': 'dwilliams@school.edu',
                'department': 'English',
                'years_experience': 10,
                'office': 'Room 115, Building C',
                'office_hours': 'Mon, Fri: 3:00 PM - 5:00 PM',
                'phone': '+44 7700 900789'
            }
        ]
        
        teachers_created = 0
        
        # Create the teachers
        for data in teacher_data:
            # Create or get user
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'email': data['email'],
                    'is_staff': True
                }
            )
            
            if created:
                user.set_password('password123')  # Set a default password
                user.save()
                teacher_group.user_set.add(user)
                teachers_created += 1
            
            # Create or get teacher profile
            teacher, created = Teacher.objects.get_or_create(
                user=user,
                defaults={
                    'department': data['department'],
                    'years_experience': data['years_experience'],
                    'office': data['office'],
                    'office_hours': data['office_hours'],
                    'phone': data['phone']
                }
            )
            
            self.stdout.write(self.style.SUCCESS(f'Created teacher: {user.get_full_name()}'))
        
        self.stdout.write(self.style.SUCCESS(f'Successfully added {teachers_created} teachers'))