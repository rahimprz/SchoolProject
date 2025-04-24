from django.db import migrations
from django.contrib.auth.models import Group
import datetime

def create_sample_data(apps, schema_editor):
    User = apps.get_model('auth', 'User')

    # Get models
    Student = apps.get_model('authentication', 'Student')
    Subject = apps.get_model('authentication', 'Subject')
    StudentSubject = apps.get_model('authentication', 'StudentSubject')
    
    # Create student group if it doesn't exist
    try:
        student_group = Group.objects.get(name='Student')
    except Group.DoesNotExist:
        student_group = Group.objects.create(name='Student')
    
    # Create subjects
    math = Subject.objects.create(name='Mathematics', teacher_name='Mr. Thompson')
    science = Subject.objects.create(name='Science', teacher_name='Ms. Johnson')
    english = Subject.objects.create(name='English', teacher_name='Mrs. Williams')
    history = Subject.objects.create(name='History', teacher_name='Mr. Davis')
    art = Subject.objects.create(name='Art', teacher_name='Ms. Roberts')
    
    # Create sample students
    sample_students = [
        {
            'username': 'john_buckle',
            'first_name': 'John',
            'last_name': 'Buckle',
            'email': 'john.buckle@example.com',
            'dob': datetime.date(2008, 7, 15),
            'parent': 'Sarah Buckle',
            'address': 'Ellon Road, Aberdeen',
            'emergency_name': 'Sarah Buckle',
            'emergency_relation': 'Mother',
            'emergency_phone': '+448629703703',
            'alt_name': 'Michael Buckle',
            'alt_relation': 'Father',
            'alt_phone': '+44700620073',
            'grades': {'Mathematics': 10.8, 'Science': 11.2, 'English': 9.5, 'History': 9.8, 'Art': 9.7}
        },
        {
            'username': 'emma_smith',
            'first_name': 'Emma',
            'last_name': 'Smith',
            'email': 'emma.smith@example.com',
            'dob': datetime.date(2008, 3, 22),
            'parent': 'Rachel Smith',
            'address': 'King Street, Aberdeen',
            'emergency_name': 'Rachel Smith',
            'emergency_relation': 'Mother',
            'emergency_phone': '+448629704567',
            'alt_name': 'Daniel Smith',
            'alt_relation': 'Father',
            'alt_phone': '+44700625555',
            'grades': {'Mathematics': 9.5, 'Science': 10.8, 'English': 11.2, 'History': 8.7, 'Art': 12.0}
        }
    ]
    
    for student_data in sample_students:
        # Create user
        try:
            user = User.objects.create(
                username=student_data['username'],
                email=student_data['email'],
                password='password123',  # Default password, should be changed
                first_name=student_data['first_name'],
                last_name=student_data['last_name']
            )
            user.set_password('password123')
            user.save()
            
            # Add to student group
            user.groups.add(student_group)
            
            # Create student profile
            student = Student.objects.create(
                user=user,
                date_of_birth=student_data['dob'],
                parent_guardian=student_data['parent'],
                address=student_data['address'],
                emergency_contact_name=student_data['emergency_name'],
                emergency_contact_relation=student_data['emergency_relation'],
                emergency_phone=student_data['emergency_phone'],
                alt_contact_name=student_data['alt_name'],
                alt_contact_relation=student_data['alt_relation'],
                alt_contact_phone=student_data['alt_phone']
            )
            
            # Create subject associations with grades
            for subject_name, grade in student_data['grades'].items():
                subject = Subject.objects.get(name=subject_name)
                StudentSubject.objects.create(
                    student=student,
                    subject=subject,
                    grade=grade
                )
        except Exception as e:
            # Skip if user already exists
            print(f"Error creating user {student_data['username']}: {e}")

def remove_sample_data(apps, schema_editor):
    # Get models
    User = apps.get_model('auth', 'User')
    Subject = apps.get_model('authentication', 'Subject')
    
    # Delete sample users and subjects
    User.objects.filter(username__in=['john_buckle', 'emma_smith']).delete()
    Subject.objects.filter(name__in=['Mathematics', 'Science', 'English', 'History', 'Art']).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0001_initial'),  # Make sure this matches your initial migration
    ]

    operations = [
        migrations.RunPython(create_sample_data, remove_sample_data),
    ]