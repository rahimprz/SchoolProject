# Script to populate database with example data
import random
from django.contrib.auth.models import User, Group
from django.utils import timezone
from datetime import timedelta, date
from authentication.models import Teacher, Student, ClassRoom, Behavior, Subject, StudentSubject, SeatingPlan, SeatAssignment

def run():
    print("Starting data population...")
    
    # Create groups if they don't exist
    print("Creating groups...")
    teacher_group, _ = Group.objects.get_or_create(name="Teacher")
    student_group, _ = Group.objects.get_or_create(name="Student")
    staff_group, _ = Group.objects.get_or_create(name="Staff")
    
    # Create example teachers
    print("Creating teachers...")
    teacher_data = [
        {
            'username': 'teacher1',
            'email': 'teacher1@example.com',
            'first_name': 'John',
            'last_name': 'Smith',
            'department': 'Science',
            'years_experience': 8,
            'office': 'Room 201',
            'office_hours': 'Mon-Wed: 3:00 PM - 4:30 PM',
            'phone': '555-123-4567'
        },
        {
            'username': 'teacher2',
            'email': 'teacher2@example.com',
            'first_name': 'Sarah',
            'last_name': 'Johnson',
            'department': 'Mathematics',
            'years_experience': 12,
            'office': 'Room 305',
            'office_hours': 'Tue-Thu: 2:30 PM - 4:00 PM',
            'phone': '555-987-6543'
        }
    ]
    
    teachers = []
    for data in teacher_data:
        user, created = User.objects.get_or_create(
            username=data['username'],
            defaults={
                'email': data['email'],
                'first_name': data['first_name'],
                'last_name': data['last_name']
            }
        )
        
        if created:
            user.set_password('password123')
            user.save()
            teacher_group.user_set.add(user)
            
        teacher, _ = Teacher.objects.get_or_create(
            user=user,
            defaults={
                'department': data['department'],
                'years_experience': data['years_experience'],
                'office': data['office'],
                'office_hours': data['office_hours'],
                'phone': data['phone']
            }
        )
        teachers.append(user)  # Store the User object for the teacher
    
    # Create subjects
    print("Creating subjects...")
    subject_data = [
        {'name': 'Mathematics', 'teacher_name': 'Sarah Johnson'},
        {'name': 'Science', 'teacher_name': 'John Smith'},
        {'name': 'English', 'teacher_name': 'Emily Davis'},
        {'name': 'History', 'teacher_name': 'Michael Brown'},
        {'name': 'Art', 'teacher_name': 'Jessica Wilson'}
    ]
    
    subjects = []
    for i, data in enumerate(subject_data):
        subject, _ = Subject.objects.get_or_create(
            name=data['name'],
            defaults={
                'teacher_name': data['teacher_name']
            }
        )
        subjects.append(subject)
    
    # Create classrooms
    print("Creating classrooms...")
    classroom_data = [
        {'name': '9A Mathematics', 'rows': 5, 'columns': 5, 'subject': subjects[0]},
        {'name': '10B Science', 'rows': 4, 'columns': 7, 'subject': subjects[1]},
        {'name': '11C English', 'rows': 4, 'columns': 6, 'subject': subjects[2]},
        {'name': '9B History', 'rows': 4, 'columns': 6, 'subject': subjects[3]},
        {'name': '10A Art', 'rows': 4, 'columns': 5, 'subject': subjects[4]}
    ]
    
    classrooms = []
    for i, data in enumerate(classroom_data):
        classroom, _ = ClassRoom.objects.get_or_create(
            name=data['name'],
            defaults={
                'teacher': teachers[i % len(teachers)],
                'rows': data['rows'],
                'columns': data['columns'],
                'subject': data['subject']
            }
        )
        classrooms.append(classroom)
    
    # Create students
    print("Creating students...")
    student_names = [
        ('Emma', 'Thompson'), ('James', 'Wilson'), ('Sophia', 'Martinez'),
        ('Ethan', 'Brown'), ('Olivia', 'Davis'), ('Noah', 'Johnson'),
        ('Ava', 'Miller'), ('William', 'Anderson'), ('Isabella', 'Taylor'),
        ('Benjamin', 'Thomas'), ('Mia', 'Jackson'), ('Lucas', 'White'),
        ('Charlotte', 'Harris'), ('Henry', 'Martin'), ('Amelia', 'Thompson'),
        ('Alexander', 'Garcia'), ('Harper', 'Martinez'), ('Michael', 'Robinson'),
        ('Evelyn', 'Clark'), ('Daniel', 'Rodriguez'), ('Abigail', 'Lewis'),
        ('Matthew', 'Lee'), ('Emily', 'Walker'), ('David', 'Hall'),
        ('Elizabeth', 'Allen'), ('Joseph', 'Young'), ('Sofia', 'Hernandez'),
        ('Carter', 'King'), ('Madison', 'Wright'), ('Jayden', 'Lopez')
    ]
    
    students = []
    for i, (first_name, last_name) in enumerate(student_names):
        username = f"{first_name.lower()}.{last_name.lower()}"
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f"{username}@example.com",
                'first_name': first_name,
                'last_name': last_name
            }
        )
        
        if created:
            user.set_password('student123')
            user.save()
            student_group.user_set.add(user)
        
        # Create student with fields that match your model
        student, _ = Student.objects.get_or_create(
            user=user,
            defaults={
                'date_of_birth': date(2005 - random.randint(0, 3), random.randint(1, 12), random.randint(1, 28)),
                'parent_guardian': f"{random.choice(['Mr.', 'Mrs.', 'Dr.'])} {last_name}",
                'address': f"{random.randint(100, 999)} {random.choice(['Maple', 'Oak', 'Pine', 'Cedar'])} {random.choice(['St', 'Ave', 'Blvd', 'Dr'])}",
                'emergency_contact_name': f"{random.choice(['Robert', 'Mary', 'James', 'Linda'])} {last_name}",
                'emergency_contact_relation': random.choice(['Father', 'Mother', 'Guardian']),
                'emergency_phone': f"555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                'theme': random.choice(['light', 'dark', 'system']),
                'color_accent': random.choice(['blue', 'green', 'purple', 'orange']),
                'font_size': random.choice(['small', 'medium', 'large'])
            }
        )
        students.append(student)
    
    # Assign students to subjects
    print("Assigning students to subjects...")
    for student in students:
        # Assign each student to 3-5 random subjects
        num_subjects = random.randint(3, 5)
        for subject in random.sample(subjects, num_subjects):
            student_subject, _ = StudentSubject.objects.get_or_create(
                student=student,
                subject=subject,
                defaults={
                    'grade': round(random.uniform(60.0, 100.0), 1)  # Random grade between 60 and 100
                }
            )
    
    # Create behavior records
    print("Creating behavior records...")
    positive_behaviors = [
        "Excellent participation in class discussion",
        "Helping classmate with difficult problem",
        "Outstanding homework submission",
        "Great teamwork during group project",
        "Volunteered to help clean up after lab",
        "Consistently prepared for class"
    ]
    
    negative_behaviors = [
        "Disrupting class with excessive talking",
        "Late to class without excuse",
        "Disrespectful behavior towards peers",
        "Unauthorized use of phone during lesson",
        "Incomplete homework assignment",
        "Sleeping during class"
    ]
    
    for _ in range(50):  # Create 50 behavior records
        student = random.choice(students)
        teacher_user = random.choice(teachers)
        subject = random.choice(subjects)
        
        # Randomly choose positive or negative behavior
        if random.choice([True, False]):
            behavior_type = 'positive'
            points = random.randint(1, 5)
            description = random.choice(positive_behaviors)
        else:
            behavior_type = 'negative'
            points = -random.randint(1, 5)
            description = random.choice(negative_behaviors)
        
        # Random date in the last 30 days
        days_ago = random.randint(0, 30)
        record_date = timezone.now() - timedelta(days=days_ago)
        
        Behavior.objects.create(
            student=student,
            subject=subject,
            behavior_type=behavior_type,
            description=description,
            points=points,
            recorded_by=f"{teacher_user.first_name} {teacher_user.last_name}",
            recorded_at=record_date
        )
    
    # Create seating plans for each classroom
    print("Creating seating plans...")
    for classroom in classrooms:
        # Get students enrolled in this subject
        enrolled_students = StudentSubject.objects.filter(
            subject=classroom.subject
        ).select_related('student')
        
        # Create a seating plan
        seating_plan, _ = SeatingPlan.objects.get_or_create(
            classroom=classroom,
            name=f"Default Plan for {classroom.name}",
            defaults={
                'is_active': True
            }
        )
        
        # Assign seats to students
        enrolled_student_list = list(enrolled_students)
        random.shuffle(enrolled_student_list)
        
        seat_count = 0
        for row in range(classroom.rows):
            for col in range(classroom.columns):
                if seat_count < len(enrolled_student_list):
                    # Assign this seat to a student
                    SeatAssignment.objects.get_or_create(
                        seating_plan=seating_plan,
                        student=enrolled_student_list[seat_count].student,
                        defaults={
                            'row': row,
                            'column': col
                        }
                    )
                    seat_count += 1

    print("Database populated with example data successfully!")

if __name__ == "__main__":
    run()
