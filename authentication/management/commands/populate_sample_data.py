from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.db import transaction
from authentication.models import Student, Subject, StudentSubject, Behavior, ClassRoom, SeatingPlan, SeatAssignment
import random
from datetime import datetime, timedelta
import string

class Command(BaseCommand):
    help = 'Populates the database with sample data for testing'

    def add_arguments(self, parser):
        parser.add_argument('--teachers', type=int, default=2, help='Number of teachers to create')
        parser.add_argument('--students', type=int, default=30, help='Number of students to create')
        parser.add_argument('--subjects', type=int, default=5, help='Number of subjects to create')
        parser.add_argument('--classrooms', type=int, default=4, help='Number of classrooms to create')
        parser.add_argument('--behaviors', type=int, default=100, help='Number of behavior records to create')

    def handle(self, *args, **options):
        num_teachers = options['teachers']
        num_students = options['students']
        num_subjects = options['subjects']
        num_classrooms = options['classrooms']
        num_behaviors = options['behaviors']

        self.stdout.write(self.style.SUCCESS('Starting sample data population...'))

        # Create groups if they don't exist
        teacher_group, _ = Group.objects.get_or_create(name='Teacher')
        student_group, _ = Group.objects.get_or_create(name='Student')
        staff_group, _ = Group.objects.get_or_create(name='Staff')

        # Create sample data within a transaction
        with transaction.atomic():
            # Create teachers
            teachers = self._create_teachers(num_teachers, teacher_group)
            
            # Create students
            students = self._create_students(num_students, student_group)
            
            # Create subjects
            subjects = self._create_subjects(num_subjects, teachers)
            
            # Create classrooms
            classrooms = self._create_classrooms(num_classrooms, subjects, teachers)
            
            # Enroll students in subjects
            self._enroll_students(students, subjects)
            
            # Create seating plans
            seating_plans = self._create_seating_plans(classrooms)
            
            # Assign seats
            self._assign_seats(seating_plans, students, subjects)
            
            # Create behavior records
            self._create_behaviors(num_behaviors, students, subjects, teachers)

        self.stdout.write(self.style.SUCCESS('Successfully populated sample data!'))
        self.stdout.write(self.style.SUCCESS(f'Created {num_teachers} teachers, {num_students} students, {num_subjects} subjects, {num_classrooms} classrooms'))
        self.stdout.write(self.style.SUCCESS(f'Created {num_behaviors} behavior records'))
        self.stdout.write(self.style.SUCCESS('Teacher logins: teacher1/password123, teacher2/password123, etc.'))
        self.stdout.write(self.style.SUCCESS('Student logins: student1/password123, student2/password123, etc.'))

    def _create_teachers(self, num_teachers, teacher_group):
        teachers = []
        for i in range(1, num_teachers + 1):
            username = f'teacher{i}'
            
            # Skip if user already exists
            if User.objects.filter(username=username).exists():
                teachers.append(User.objects.get(username=username))
                continue
                
            user = User.objects.create_user(
                username=username,
                email=f'teacher{i}@example.com',
                password='password123',
                first_name=f'Teacher{i}',
                last_name=f'Surname{i}'
            )
            user.groups.add(teacher_group)
            teachers.append(user)
            self.stdout.write(f'Created teacher: {username}')
            
        return teachers

    def _create_students(self, num_students, student_group):
        students = []
        for i in range(1, num_students + 1):
            username = f'student{i}'
            
            # Skip if user already exists
            if User.objects.filter(username=username).exists():
                user = User.objects.get(username=username)
                student, created = Student.objects.get_or_create(user=user)
                if not created:
                    students.append(student)
                    continue
            else:
                user = User.objects.create_user(
                    username=username,
                    email=f'student{i}@example.com',
                    password='password123',
                    first_name=f'Student{i}',
                    last_name=f'Surname{i}'
                )
                user.groups.add(student_group)
                
            # Create or update student profile
            student, created = Student.objects.get_or_create(
                user=user,
                defaults={
                    'date_of_birth': datetime.now() - timedelta(days=365 * random.randint(14, 18)),
                    'parent_guardian': f'Parent of Student{i}',
                    'address': f'{random.randint(1, 100)} Sample Street, City',
                    'emergency_contact_name': f'Emergency Contact {i}',
                    'emergency_contact_relation': random.choice(['Parent', 'Guardian', 'Sibling']),
                    'emergency_phone': f'555-{random.randint(1000, 9999)}',
                }
            )
            students.append(student)
            self.stdout.write(f'Created student: {username}')
            
        return students

    def _create_subjects(self, num_subjects, teachers):
        subject_names = [
            'Mathematics', 'English', 'Science', 'History', 'Geography',
            'Physics', 'Chemistry', 'Biology', 'Computer Science', 'Art',
            'Music', 'Physical Education', 'Foreign Languages', 'Economics', 'Psychology'
        ]
        
        subjects = []
        for i in range(min(num_subjects, len(subject_names))):
            teacher = random.choice(teachers)
            subject, created = Subject.objects.get_or_create(
                name=subject_names[i],
                defaults={
                    'teacher_name': f'{teacher.first_name} {teacher.last_name}'
                }
            )
            subjects.append(subject)
            if created:
                self.stdout.write(f'Created subject: {subject.name}')
            
        return subjects

    def _create_classrooms(self, num_classrooms, subjects, teachers):
        classroom_names = [
            'Room 101', 'Room 102', 'Room 103', 'Room 104', 'Room 105',
            'Lab 1', 'Lab 2', 'Auditorium', 'Library', 'Gymnasium'
        ]
        
        classrooms = []
        for i in range(min(num_classrooms, len(classroom_names))):
            subject = random.choice(subjects)
            teacher = random.choice(teachers)
            
            classroom, created = ClassRoom.objects.get_or_create(
                name=classroom_names[i],
                subject=subject,
                defaults={
                    'teacher': teacher,
                    'rows': random.randint(3, 6),
                    'columns': random.randint(4, 8)
                }
            )
            classrooms.append(classroom)
            if created:
                self.stdout.write(f'Created classroom: {classroom.name} for {subject.name}')
            
        return classrooms

    def _enroll_students(self, students, subjects):
        # Each student is enrolled in 3-5 subjects
        for student in students:
            # Get current enrollments
            current_subjects = set(StudentSubject.objects.filter(
                student=student).values_list('subject_id', flat=True))
            
            # Determine how many more subjects to enroll in
            target_enrollments = random.randint(3, min(5, len(subjects)))
            num_to_add = max(0, target_enrollments - len(current_subjects))
            
            # Get available subjects (not already enrolled)
            available_subjects = [s for s in subjects if s.id not in current_subjects]
            
            # Enroll in random subjects
            for subject in random.sample(available_subjects, min(num_to_add, len(available_subjects))):
                enrollment, created = StudentSubject.objects.get_or_create(
                    student=student,
                    subject=subject,
                    defaults={
                        'grade': round(random.uniform(60.0, 100.0), 1)
                    }
                )
                if created:
                    self.stdout.write(f'Enrolled {student.user.username} in {subject.name}')

    def _create_seating_plans(self, classrooms):
        seating_plans = []
        for classroom in classrooms:
            # Create an active seating plan
            seating_plan, created = SeatingPlan.objects.get_or_create(
                classroom=classroom,
                is_active=True,
                defaults={
                    'name': f'Current Plan - {classroom.name}'
                }
            )
            seating_plans.append(seating_plan)
            
            if created:
                self.stdout.write(f'Created seating plan: {seating_plan.name}')
                
            # Create 1-2 saved seating plans
            for i in range(random.randint(1, 2)):
                saved_plan, created = SeatingPlan.objects.get_or_create(
                    classroom=classroom,
                    name=f'Saved Plan {i+1} - {classroom.name}',
                    defaults={
                        'is_active': False
                    }
                )
                seating_plans.append(saved_plan)
                if created:
                    self.stdout.write(f'Created saved seating plan: {saved_plan.name}')
            
        return seating_plans

    def _assign_seats(self, seating_plans, students, subjects):
        for seating_plan in seating_plans:
            # Get students enrolled in this subject
            enrolled_students = []
            for student in students:
                if StudentSubject.objects.filter(student=student, subject=seating_plan.classroom.subject).exists():
                    enrolled_students.append(student)
            
            if not enrolled_students:
                continue
                
            # Clear existing assignments
            SeatAssignment.objects.filter(seating_plan=seating_plan).delete()
            
            # Randomly assign seats
            random.shuffle(enrolled_students)
            seat_count = 0
            for row in range(seating_plan.classroom.rows):
                for col in range(seating_plan.classroom.columns):
                    if seat_count < len(enrolled_students):
                        SeatAssignment.objects.create(
                            seating_plan=seating_plan,
                            student=enrolled_students[seat_count],
                            row=row,
                            column=col
                        )
                        seat_count += 1
            
            self.stdout.write(f'Assigned {seat_count} students to seats in {seating_plan.name}')

    def _create_behaviors(self, num_behaviors, students, subjects, teachers):
        positive_reasons = [
            'Excellent participation in class',
            'Helping other students',
            'Outstanding homework submission',
            'Great teamwork',
            'Improved performance',
            'Perfect attendance',
            'Exceptional project work',
            'Positive attitude',
            'Going above and beyond',
            'Leadership in group activities'
        ]
        
        negative_reasons = [
            'Disruptive behavior',
            'Late assignment submission',
            'Unauthorized device use',
            'Tardiness',
            'Incomplete homework',
            'Disrespectful behavior',
            'Not following instructions',
            'Excessive talking',
            'Unprepared for class',
            'Poor participation'
        ]
        
        # Delete existing behaviors if requested
        existing_count = Behavior.objects.count()
        if existing_count > 500:  # Safety check to avoid deleting too much data
            self.stdout.write(self.style.WARNING(f'Skipping behavior creation - too many existing records ({existing_count})'))
            return
            
        # Create new behaviors
        for _ in range(num_behaviors):
            student = random.choice(students)
            subject = random.choice(subjects)
            teacher = random.choice(teachers)
            
            # Determine if positive or negative
            is_positive = random.random() > 0.3  # 70% positive, 30% negative
            
            if is_positive:
                behavior_type = 'positive'
                points = random.randint(1, 5)
                description = random.choice(positive_reasons)
            else:
                behavior_type = 'negative'
                points = -random.randint(1, 3)
                description = random.choice(negative_reasons)
                
            # Random date in the last 90 days
            recorded_at = datetime.now() - timedelta(days=random.randint(0, 90))
            
            behavior = Behavior.objects.create(
                student=student,
                subject=subject,
                behavior_type=behavior_type,
                description=description,
                points=points,
                recorded_by=f'{teacher.first_name} {teacher.last_name}',
                recorded_at=recorded_at
            )
            
        self.stdout.write(f'Created {num_behaviors} behavior records')
