from django.db import models
from django.contrib.auth.models import User

class Subject(models.Model):
    name = models.CharField(max_length=100)
    teacher_name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    date_of_birth = models.DateField(null=True, blank=True)
    parent_guardian = models.CharField(max_length=100, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    emergency_contact_name = models.CharField(max_length=100, null=True, blank=True)
    emergency_contact_relation = models.CharField(max_length=50, null=True, blank=True)
    emergency_phone = models.CharField(max_length=20, null=True, blank=True)
    alt_contact_name = models.CharField(max_length=100, null=True, blank=True)
    alt_contact_relation = models.CharField(max_length=50, null=True, blank=True)
    alt_contact_phone = models.CharField(max_length=20, null=True, blank=True)
    
    # Notification preferences
    email_assignments = models.BooleanField(default=True)
    email_grades = models.BooleanField(default=True)
    email_announcements = models.BooleanField(default=True)
    email_reminders = models.BooleanField(default=True)
    push_assignments = models.BooleanField(default=True)
    push_grades = models.BooleanField(default=True)
    push_announcements = models.BooleanField(default=True)
    push_reminders = models.BooleanField(default=True)
    
    # Appearance settings
    theme = models.CharField(max_length=20, default='light', choices=[
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('system', 'System Default')
    ])
    color_accent = models.CharField(max_length=20, default='blue', choices=[
        ('blue', 'Blue'),
        ('green', 'Green'),
        ('purple', 'Purple'),
        ('orange', 'Orange')
    ])
    font_size = models.CharField(max_length=20, default='medium', choices=[
        ('small', 'Small'),
        ('medium', 'Medium'),
        ('large', 'Large')
    ])
    
    # Privacy settings
    profile_visibility = models.CharField(max_length=20, default='staff', choices=[
        ('public', 'Public'),
        ('staff', 'Staff Only'),
        ('private', 'Private')
    ])
    analytics_allowed = models.BooleanField(default=True)
    data_sharing = models.BooleanField(default=True)
    
    def __str__(self):
        return self.user.username

class StudentSubject(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='subjects')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    grade = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    
    def __str__(self):
        return f"{self.student.user.username} - {self.subject.name}"


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=100, blank=True)
    years_experience = models.IntegerField(default=0)
    office = models.CharField(max_length=100, blank=True)
    office_hours = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    def __str__(self):
        return self.user.get_full_name() or self.user.username


class Behavior(models.Model):
    BEHAVIOR_TYPES = [
        ('positive', 'Positive'),
        ('negative', 'Negative')
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='behaviors')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, null=True, blank=True)
    behavior_type = models.CharField(max_length=10, choices=BEHAVIOR_TYPES)
    description = models.TextField()
    points = models.IntegerField()
    recorded_by = models.CharField(max_length=100)
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.student.user.username} - {self.behavior_type} - {self.points} points"
        
class ClassRoom(models.Model):
    name = models.CharField(max_length=100)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'groups__name': 'Teacher'})
    rows = models.IntegerField(default=3)
    columns = models.IntegerField(default=4)
    
    def __str__(self):
        return f"{self.name} - {self.subject.name}"

class SeatingPlan(models.Model):
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='seating_plans')
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.classroom.name} - {self.name}"

class SeatAssignment(models.Model):
    seating_plan = models.ForeignKey(SeatingPlan, on_delete=models.CASCADE, related_name='seat_assignments')
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    row = models.IntegerField()
    column = models.IntegerField()
    
    class Meta:
        unique_together = ('seating_plan', 'row', 'column')
        unique_together = ('seating_plan', 'student')
    
    def __str__(self):
        return f"{self.seating_plan.name} - {self.student.user.username} - Row {self.row}, Column {self.column}"
        
        
class BehaviorRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='behavior_records')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    points = models.IntegerField()
    description = models.TextField()
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.student} - {self.points} points - {self.recorded_at.strftime('%Y-%m-%d')}"

class Assignment(models.Model):
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    points_possible = models.IntegerField(default=100)
    due_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.title
        
