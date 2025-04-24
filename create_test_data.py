import os
import django
import sys

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')  # Change if your settings module is different
django.setup()

from django.contrib.auth.models import User, Group
from authentication.models import Student, Subject, ClassRoom, SeatingPlan

def create_test_classroom():
    # Get the logged-in teacher
    username = input("Enter your teacher username: ")
    
    try:
        teacher = User.objects.get(username=username)
        print(f"Found teacher: {teacher.username}")
        
        # Make sure teacher is in Teacher group
        teacher_group, _ = Group.objects.get_or_create(name='Teacher')
        if not teacher.groups.filter(name='Teacher').exists():
            teacher.groups.add(teacher_group)
            print("Added user to Teacher group")
        
        # Create a subject
        subject_name = input("Enter subject name (e.g., Mathematics): ")
        subject, created = Subject.objects.get_or_create(
            name=subject_name,
            defaults={'teacher_name': f"{teacher.first_name} {teacher.last_name}"}
        )
        if created:
            print(f"Created subject: {subject.name}")
        else:
            print(f"Using existing subject: {subject.name}")
        
        # Create a classroom
        classroom_name = input("Enter classroom name (e.g., Room 101): ")
        classroom, created = ClassRoom.objects.get_or_create(
            name=classroom_name,
            subject=subject,
            defaults={
                'teacher': teacher,
                'rows': 4,
                'columns': 5
            }
        )
        
        if created:
            print(f"Created classroom: {classroom.name}")
        else:
            print(f"Using existing classroom: {classroom.name}")
            # Update teacher if needed
            if classroom.teacher != teacher:
                classroom.teacher = teacher
                classroom.save()
                print(f"Updated classroom teacher to {teacher.username}")
        
        # Create a seating plan
        seating_plan, created = SeatingPlan.objects.get_or_create(
            classroom=classroom,
            is_active=True,
            defaults={'name': f'Current Plan - {classroom.name}'}
        )
        
        if created:
            print(f"Created seating plan: {seating_plan.name}")
        else:
            print(f"Using existing seating plan: {seating_plan.name}")
        
        print("\nSetup complete! You should now be able to see the classroom in the seating plan page.")
        print(f"Go to the seating plan page and select '{classroom.name}' from the dropdown.")
        
    except User.DoesNotExist:
        print(f"Error: Teacher with username '{username}' not found.")
        sys.exit(1)

if __name__ == "__main__":
    create_test_classroom()
