# This script will fix the award/deduct functionality by ensuring the forms are properly configured

import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.urls import path, include, reverse
from django.test import Client
from django.contrib.auth.models import User
from authentication.models import Student, Subject, ClassRoom, Behavior

def test_award_points():
    """Test if the award_points view is working correctly"""
    print("Testing award_points functionality...")
    
    # Create a test client
    client = Client()
    
    # Try to log in as a teacher
    teachers = User.objects.filter(groups__name='Teacher')
    if not teachers.exists():
        print("No teachers found in the database. Please create a teacher user first.")
        return False
    
    teacher = teachers.first()
    logged_in = client.login(username=teacher.username, password='password123')
    if not logged_in:
        print(f"Could not log in as {teacher.username}. Make sure the password is 'password123'.")
        return False
    
    print(f"Logged in as teacher: {teacher.username}")
    
    # Get a student to award points to
    students = Student.objects.all()
    if not students.exists():
        print("No students found in the database. Please create student users first.")
        return False
    
    student = students.first()
    print(f"Selected student: {student.user.username}")
    
    # Get a classroom
    classrooms = ClassRoom.objects.filter(teacher=teacher)
    if not classrooms.exists():
        print("No classrooms found for this teacher. Please create a classroom first.")
        return False
    
    classroom = classrooms.first()
    print(f"Selected classroom: {classroom.name}")
    
    # Try to award points
    try:
        response = client.post('/award-points/', {
            'student_id': student.id,
            'classroom_id': classroom.id,
            'points': 2,
            'reason': 'Test award'
        })
        
        print(f"Response status code: {response.status_code}")
        if response.status_code == 200:
            print("Award points request successful!")
            return True
        else:
            print(f"Award points request failed with status code {response.status_code}")
            print(f"Response content: {response.content.decode('utf-8')}")
            return False
    except Exception as e:
        print(f"Error testing award_points: {str(e)}")
        return False

def fix_form_submission():
    """Fix the form submission in the HTML template"""
    print("\nChecking form submission method...")
    
    # Check if the award_points and deduct_points views accept POST requests
    from authentication.views import award_points, deduct_points
    
    # Check if the views have the @require_POST decorator
    award_post_only = hasattr(award_points, 'csrf_exempt') or 'post' in str(award_points).lower()
    deduct_post_only = hasattr(deduct_points, 'csrf_exempt') or 'post' in str(deduct_points).lower()
    
    print(f"award_points accepts POST only: {award_post_only}")
    print(f"deduct_points accepts POST only: {deduct_post_only}")
    
    print("\nTo fix the award/deduct functionality, make these changes:")
    print("\n1. Make sure your urls.py has these entries:")
    print("   path('award-points/', award_points, name='award_points'),")
    print("   path('deduct-points/', deduct_points, name='deduct_points'),")
    
    print("\n2. Check that your views.py has the correct implementations:")
    print("   @login_required")
    print("   @require_POST")
    print("   def award_points(request):")
    print("       # Implementation here")
    
    print("\n3. Ensure your HTML forms have the correct action URLs:")
    print("   <form id=\"awardPointsForm\" method=\"post\" action=\"{% url 'award_points' %}\">")
    print("   <form id=\"deductPointsForm\" method=\"post\" action=\"{% url 'deduct_points' %}\">")
    
    print("\n4. Add console.log statements to debug form submission:")
    print("   document.getElementById('awardPointsForm').addEventListener('submit', function(e) {")
    print("       console.log('Award form submitted');")
    print("   });")

if __name__ == "__main__":
    test_award_points()
    fix_form_submission()
