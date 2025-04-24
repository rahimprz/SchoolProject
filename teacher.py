from django.db import migrations
import random

def add_teacher_data(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    Group = apps.get_model('auth', 'Group')
    Teacher = apps.get_model('authentication', 'Teacher')
    Subject = apps.get_model('authentication', 'Subject')
    ClassRoom = apps.get_model('authentication', 'ClassRoom')

    teacher_group, _ = Group.objects.get_or_create(name='Teacher')

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
            'phone': '+44 7700 900123',
            'subjects': ['Mathematics', 'Advanced Mathematics']
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
            'phone': '+44 7700 900456',
            'subjects': ['Science', 'Biology']
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
            'phone': '+44 7700 900789',
            'subjects': ['English', 'Literature']
        }
    ]

    for data in teacher_data:
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

        for subject_name in data['subjects']:
            subject, _ = Subject.objects.get_or_create(
                name=subject_name,
                defaults={
                    'description': f'Study of {subject_name}'
                }
            )

            for grade in [9, 10, 11]:
                section = random.choice(['A', 'B', 'C'])
                ClassRoom.objects.get_or_create(
                    name=f'{grade}{section} {subject_name}',
                    defaults={
                        'teacher': user,
                        'subject': subject,
                        'rows': random.randint(5, 8),
                        'columns': random.randint(5, 8),
                        'capacity': random.randint(20, 30)
                    }
                )

class Migration(migrations.Migration):
    dependencies = [
        ('authentication', '0001_initial'),  # Or latest migration if applicable
    ]

    operations = [
        migrations.RunPython(add_teacher_data),
    ]
