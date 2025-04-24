from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Group
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Q
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .forms import TeacherProfileForm, NotificationSettingsForm, DisplaySettingsForm, CustomPasswordChangeForm
import logging
from .models import Student, Subject, StudentSubject, Behavior, ClassRoom, SeatingPlan, SeatAssignment, Teacher
import json
import random
from datetime import datetime, timedelta


# Set up logging
logger = logging.getLogger(__name__)

@sensitive_post_parameters()
@csrf_protect
@never_cache
def login_view(request):
    """
    Handle user login with proper error handling and role-based redirection
    """
    # If user is already authenticated, redirect to appropriate dashboard
    if request.user.is_authenticated:
        return redirect_based_on_role(request.user)
        
    context = {}
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        
        # Basic validation for empty fields
        if not username or not password:
            logger.warning(f"Login attempt with empty fields from IP: {get_client_ip(request)}")
            context["error"] = "Username and password are required"
            return render(request, "frontend/pages/AppLogin/index.html", context)
        
        # Attempt authentication
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Check if account is active
            if not user.is_active:
                logger.warning(f"Login attempt for inactive account: {username} from IP: {get_client_ip(request)}")
                context["error"] = "This account has been disabled. Please contact support."
                return render(request, "frontend/pages/AppLogin/index.html", context)
                
            # Log successful login
            logger.info(f"Successful login: {username} with role(s): {', '.join([g.name for g in user.groups.all()])}")
            
            # Login user
            login(request, user)
            
            # Redirect based on role
            return redirect_based_on_role(user)
        else:
            # Log failed login attempt
            logger.warning(f"Failed login attempt for username: {username} from IP: {get_client_ip(request)}")
            context["error"] = "Invalid username or password"
            
    return render(request, "frontend/pages/AppLogin/index.html", context)

def redirect_based_on_role(user):
    """
    Helper function to redirect users based on their role
    """
    if user.groups.filter(name="Student").exists():
        return redirect("student_profile")
    elif user.groups.filter(name__in=["Teacher", "Staff"]).exists():
        return redirect("teacher_profile")
    elif user.is_superuser:
        return redirect("admin:index")
    else:
        # Handle users with no assigned roles
        logger.warning(f"User {user.username} has no valid role assigned")
        return redirect("role_error")

def role_error(request):
    """
    View for users with no valid role assignment
    """
    return render(request, "frontend/pages/AppLogin/role_error.html")

@login_required
def seating_plan(request):
    # For debugging
    print(f"User: {request.user.username}, Groups: {[g.name for g in request.user.groups.all()]}")
    
    # Remove this block to allow students to access the seating plan
    # if request.user.groups.filter(name="Student").exists():
    #     logger.warning(f"Student {request.user.username} attempted to access seating plan")
    #     raise PermissionDenied("Students cannot access the seating plan.")
    
    # Get all classrooms for this teacher
    classrooms = ClassRoom.objects.filter(teacher=request.user)
    
    # Get the selected classroom (default to the first one)
    selected_classroom_id = request.GET.get('classroom', None)
    
    if selected_classroom_id and selected_classroom_id.isdigit():
        try:
            selected_classroom = classrooms.get(id=int(selected_classroom_id))
        except ClassRoom.DoesNotExist:
            selected_classroom = classrooms.first() if classrooms.exists() else None
    else:
        selected_classroom = classrooms.first() if classrooms.exists() else None
    
    # Get the active seating plan for the selected classroom
    active_seating_plan = None
    seat_assignments = []
    unassigned_students = []
    
    if selected_classroom:
        # Get all students enrolled in this subject
        enrolled_students = StudentSubject.objects.filter(
            subject=selected_classroom.subject
        ).select_related('student__user')
        
        # Get the active seating plan
        try:
            active_seating_plan = SeatingPlan.objects.get(
                classroom=selected_classroom,
                is_active=True
            )
            
            # Get seat assignments for this plan
            seat_assignments = SeatAssignment.objects.filter(
                seating_plan=active_seating_plan
            ).select_related('student__user')
            
            # Get assigned student IDs
            assigned_student_ids = seat_assignments.values_list('student_id', flat=True)
            
            # Get unassigned students
            unassigned_students = [
                enrollment.student for enrollment in enrolled_students
                if enrollment.student.id not in assigned_student_ids
            ]
            
        except SeatingPlan.DoesNotExist:
            # No active seating plan, all students are unassigned
            unassigned_students = [enrollment.student for enrollment in enrolled_students]
    
    # Get behavior data for all students
    student_ids = [s.id for s in unassigned_students]
    if seat_assignments:
        student_ids.extend([sa.student.id for sa in seat_assignments])
    
    # Get total points for each student
    student_points = {}
    if student_ids:
        behaviors = Behavior.objects.filter(student_id__in=student_ids)
        
        for student_id in student_ids:
            student_behaviors = behaviors.filter(student_id=student_id)
            total_points = sum(b.points for b in student_behaviors)
            student_points[student_id] = total_points
    
    # Get recent behavior for each student
    student_recent_behavior = {}
    if student_ids:
        for student_id in student_ids:
            recent = Behavior.objects.filter(student_id=student_id).order_by('-recorded_at').first()
            if recent:
                student_recent_behavior[student_id] = recent.description
    
    # Calculate behavior categories (green, orange, red)
    if student_points:
        all_points = sorted(student_points.values(), reverse=True)
        total_students = len(all_points)
        
        # Top 50%
        green_threshold = all_points[int(total_students * 0.5) - 1] if total_students > 1 else 0
        
        # Next 25%
        orange_threshold = all_points[int(total_students * 0.75) - 1] if total_students > 3 else 0
        
        # Bottom 25% is red
    else:
        green_threshold = 0
        orange_threshold = 0
    
    # Prepare seat grid
    seat_grid = []
    if selected_classroom:
        for row in range(selected_classroom.rows):
            seat_row = []
            for col in range(selected_classroom.columns):
                # Find if there's a student assigned to this seat
                assigned_student = None
                for assignment in seat_assignments:
                    if assignment.row == row and assignment.column == col:
                        assigned_student = assignment.student
                        break
                
                seat_row.append({
                    'row': row,
                    'column': col,
                    'student': assigned_student,
                    'points': student_points.get(assigned_student.id, 0) if assigned_student else 0,
                    'recent_behavior': student_recent_behavior.get(assigned_student.id, '') if assigned_student else '',
                    'category': 'green' if assigned_student and student_points.get(assigned_student.id, 0) >= green_threshold else
                               'orange' if assigned_student and student_points.get(assigned_student.id, 0) >= orange_threshold else
                               'red' if assigned_student else ''
                })
            seat_grid.append(seat_row)
    
    context = {
        'classrooms': classrooms,
        'selected_classroom': selected_classroom,
        'active_seating_plan': active_seating_plan,
        'seat_grid': seat_grid,
        'unassigned_students': [
            {
                'student': student,
                'points': student_points.get(student.id, 0),
                'recent_behavior': student_recent_behavior.get(student.id, ''),
                'category': 'green' if student_points.get(student.id, 0) >= green_threshold else
                           'orange' if student_points.get(student.id, 0) >= orange_threshold else
                           'red'
            }
            for student in unassigned_students
        ],
        'green_threshold': green_threshold,
        'orange_threshold': orange_threshold
    }
    
    return render(request, "frontend/pages/SeatingPlan/index.html", context)

@login_required
@require_POST
def award_points(request):
    """Award behavior points to a student."""
    try:
        # Add debugging
        print("award_points called")
        print(f"POST data: {request.POST}")
        
        student_id = request.POST.get('student_id')
        points = int(request.POST.get('points', 1))
        reason = request.POST.get('reason')
        custom_reason = request.POST.get('custom_reason')
        
        # Use custom reason if provided
        if reason == 'Other' and custom_reason:
            reason = custom_reason
            
        # Get the student
        student = Student.objects.get(id=student_id)
        
        # Get the classroom and subject
        classroom_id = request.POST.get('classroom_id')
        classroom = ClassRoom.objects.get(id=classroom_id)
        subject = classroom.subject
        
        # Create behavior record
        behavior = Behavior.objects.create(
            student=student,
            subject=subject,
            behavior_type='positive',
            description=reason,
            points=points,
            recorded_by=request.user.get_full_name() or request.user.username
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Awarded {points} points to {student.user.get_full_name()}',
            'behavior_id': behavior.id
        })
    except Exception as e:
        logger.error(f"Error awarding points: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@require_POST
def deduct_points(request):
    """Deduct behavior points from a student."""
    try:
        # Add debugging
        print("deduct_points called")
        print(f"POST data: {request.POST}")
        
        student_id = request.POST.get('student_id')
        points = int(request.POST.get('points', -1))  # Should be negative
        reason = request.POST.get('reason')
        custom_reason = request.POST.get('custom_reason')
        
        # Use custom reason if provided
        if reason == 'Other' and custom_reason:
            reason = custom_reason
            
        # Get the student
        student = Student.objects.get(id=student_id)
        
        # Get the classroom and subject
        classroom_id = request.POST.get('classroom_id')
        classroom = ClassRoom.objects.get(id=classroom_id)
        subject = classroom.subject
        
        # Create behavior record
        behavior = Behavior.objects.create(
            student=student,
            subject=subject,
            behavior_type='negative',
            description=reason,
            points=points,  # This should be a negative number
            recorded_by=request.user.get_full_name() or request.user.username
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Deducted {abs(points)} points from {student.user.get_full_name()}',
            'behavior_id': behavior.id
        })
    except Exception as e:
        logger.error(f"Error deducting points: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@require_POST
def update_seat_assignment(request):
    """Update a student's seat assignment."""
    try:
        data = json.loads(request.body)
        student_id = data.get('student_id')
        seating_plan_id = data.get('seating_plan_id')
        row = int(data.get('row'))
        column = int(data.get('column'))
        
        # Get the student and seating plan
        student = Student.objects.get(id=student_id)
        seating_plan = SeatingPlan.objects.get(id=seating_plan_id)
        
        # Check if this seat is already occupied
        existing_assignment = SeatAssignment.objects.filter(
            seating_plan=seating_plan,
            row=row,
            column=column
        ).first()
        
        if existing_assignment:
            return JsonResponse({
                'success': False,
                'error': 'This seat is already occupied'
            })
        
        # Check if this student already has a seat
        existing_student_assignment = SeatAssignment.objects.filter(
            seating_plan=seating_plan,
            student=student
        ).first()
        
        if existing_student_assignment:
            # Update the existing assignment
            existing_student_assignment.row = row
            existing_student_assignment.column = column
            existing_student_assignment.save()
        else:
            # Create a new assignment
            SeatAssignment.objects.create(
                seating_plan=seating_plan,
                student=student,
                row=row,
                column=column
            )
        
        return JsonResponse({
            'success': True,
            'message': f'Updated seat assignment for {student.user.get_full_name()}'
        })
    except Exception as e:
        logger.error(f"Error updating seat assignment: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def get_student_profile(request):
    """Get a student's profile data for the modal."""
    try:
        student_id = request.GET.get('student_id')
        student = Student.objects.get(id=student_id)
        
        # Get behavior records
        behaviors = Behavior.objects.filter(student=student).order_by('-recorded_at')[:10]
        
        # Calculate total points
        total_points = sum(b.points for b in Behavior.objects.filter(student=student))
        
        # Format activities for the response
        activities = []
        for behavior in behaviors:
            activities.append({
                'points': behavior.points,
                'description': behavior.description,
                'date': behavior.recorded_at.strftime('%b %d, %Y %I:%M %p')
            })
        
        return JsonResponse({
            'success': True,
            'total_points': total_points,
            'activities': activities
        })
    except Exception as e:
        logger.error(f"Error getting student profile: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@require_POST
def randomize_seating(request):
    """Randomize the seating plan for a classroom."""
    try:
        data = json.loads(request.body)
        classroom_id = data.get('classroom_id')
        
        # Get the classroom
        classroom = ClassRoom.objects.get(id=classroom_id)
        
        # Get or create an active seating plan
        seating_plan, created = SeatingPlan.objects.get_or_create(
            classroom=classroom,
            is_active=True,
            defaults={'name': 'Randomized Plan'}
        )
        
        if not created:
            # Clear existing assignments
            SeatAssignment.objects.filter(seating_plan=seating_plan).delete()
        
        # Get all students enrolled in this subject
        enrolled_students = StudentSubject.objects.filter(
            subject=classroom.subject
        ).select_related('student__user')
        
        students = [enrollment.student for enrollment in enrolled_students]
        random.shuffle(students)
        
        # Assign seats
        seat_count = 0
        for row in range(classroom.rows):
            for col in range(classroom.columns):
                if seat_count < len(students):
                    SeatAssignment.objects.create(
                        seating_plan=seating_plan,
                        student=students[seat_count],
                        row=row,
                        column=col
                    )
                    seat_count += 1
        
        return JsonResponse({
            'success': True,
            'message': 'Seating plan randomized successfully'
        })
    except Exception as e:
        logger.error(f"Error randomizing seating: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@require_POST
def save_seating_plan(request):
    """Save the current seating plan with a new name."""
    try:
        data = json.loads(request.body)
        classroom_id = data.get('classroom_id')
        plan_name = data.get('plan_name')
        
        # Get the classroom
        classroom = ClassRoom.objects.get(id=classroom_id)
        
        # Get the active seating plan
        active_plan = SeatingPlan.objects.get(
            classroom=classroom,
            is_active=True
        )
        
        # Create a new seating plan with the same assignments
        new_plan = SeatingPlan.objects.create(
            classroom=classroom,
            name=plan_name,
            is_active=False
        )
        
        # Copy seat assignments
        for assignment in SeatAssignment.objects.filter(seating_plan=active_plan):
            SeatAssignment.objects.create(
                seating_plan=new_plan,
                student=assignment.student,
                row=assignment.row,
                column=assignment.column
            )
        
        return JsonResponse({
            'success': True,
            'message': f'Seating plan "{plan_name}" saved successfully'
        })
    except Exception as e:
        logger.error(f"Error saving seating plan: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@permission_required('authentication.view_seatingplan', raise_exception=True)
@login_required
def behaviour_history(request):
    return render(request, "frontend/pages/BehaviourHistory/index.html")

def login_faq(request):
    return render(request, "frontend/pages/FAQsLogin/index.html")

@login_required
def logout_view(request):
    username = request.user.username
    logout(request)
    logger.info(f"User {username} logged out")
    messages.success(request, "You have been successfully logged out.")
    return redirect("login")

@login_required
def teacher_profile(request):
    if not request.user.groups.filter(name__in=["Teacher", "Staff"]).exists():
        logger.warning(f"Unauthorized access attempt to teacher profile by {request.user.username}")
        return redirect('login')
    
    try:
        # Get teacher data
        try:
            teacher = Teacher.objects.get(user=request.user)
            
            # Get classrooms taught by this teacher
            classrooms = ClassRoom.objects.filter(teacher=request.user)
            
            # Count total students
            total_students = 0
            for classroom in classrooms:
                enrolled_students = StudentSubject.objects.filter(subject=classroom.subject).count()
                total_students += enrolled_students
            
            # Get behavior scores for each class
            class_behavior_scores = {}
            for classroom in classrooms:
                # Get students enrolled in this subject
                enrolled_students = StudentSubject.objects.filter(
                    subject=classroom.subject
                ).values_list('student_id', flat=True)
                
                # Get average behavior score for these students
                if enrolled_students:
                    behaviors = Behavior.objects.filter(student_id__in=enrolled_students)
                    student_points = {}
                    
                    for student_id in enrolled_students:
                        student_behaviors = behaviors.filter(student_id=student_id)
                        total_points = sum(b.points for b in student_behaviors)
                        student_points[student_id] = total_points
                    
                    if student_points:
                        avg_score = sum(student_points.values()) / len(student_points)
                        # Normalize to a 0-100 scale
                        normalized_score = min(100, max(0, 75 + avg_score))
                        class_behavior_scores[classroom.name] = round(normalized_score)
                    else:
                        class_behavior_scores[classroom.name] = 85
                else:
                    class_behavior_scores[classroom.name] = 85
            
            # Calculate average behavior score
            average_behavior_score = round(sum(class_behavior_scores.values()) / len(class_behavior_scores)) if class_behavior_scores else 85
            
            # Get recent behavior records
            recent_behaviors = Behavior.objects.filter(
                recorded_by__contains=f"{request.user.first_name} {request.user.last_name}"
            ).select_related('student__user').order_by('-recorded_at')[:5]
            
            # Get students requiring attention (low behavior scores)
            students_requiring_attention = []
            for classroom in classrooms:
                enrolled_students = StudentSubject.objects.filter(
                    subject=classroom.subject
                ).values_list('student_id', flat=True)
                
                if enrolled_students:
                    behaviors = Behavior.objects.filter(student_id__in=enrolled_students)
                    student_points = {}
                    
                    for student_id in enrolled_students:
                        student_behaviors = behaviors.filter(student_id=student_id)
                        total_points = sum(b.points for b in student_behaviors)
                        student_points[student_id] = total_points
                    
                    # Find students with low points
                    for student_id, points in student_points.items():
                        if points < -3:  # Threshold for "requiring attention"
                            student = Student.objects.get(id=student_id)
                            students_requiring_attention.append({
                                'id': student.id,
                                'name': student.user.get_full_name() or student.user.username,
                                'class': classroom.name,
                                'behavior_score': min(100, max(0, 75 + points)),
                                'points': points
                            })
            
            # Sort by points (ascending) and limit to 4
            students_requiring_attention.sort(key=lambda x: x['points'])
            students_requiring_attention = students_requiring_attention[:4]
            
            # Get pending assignments (placeholder - replace with your actual Assignment model)
            pending_assessments = random.randint(5, 15)
            
        except (Teacher.DoesNotExist, Exception) as e:
            # Fallback to mock data if database models aren't fully set up yet
            logger.warning(f"Using mock data due to error: {str(e)}")
            
            # Create teacher with default values if it doesn't exist
            teacher, created = Teacher.objects.get_or_create(
                user=request.user,
                defaults={
                    'department': 'General',
                    'years_experience': 5,
                    'office': 'Main Building',
                    'office_hours': 'Mon-Fri: 9:00 AM - 5:00 PM',
                    'phone': '555-123-4567'
                }
            )
            
            # Generate mock classroom data
            classrooms = []
            for i in range(5):
                subject = random.choice(['Mathematics', 'Science', 'English', 'History', 'Art'])
                grade = random.choice([9, 10, 11])
                section = random.choice(['A', 'B', 'C'])
                classrooms.append({
                    'id': i + 1,
                    'name': f'{grade}{section} {subject}',
                    'rows': random.randint(4, 6),
                    'columns': random.randint(5, 7)
                })
            
            # Count total students (estimate based on classroom size)
            total_students = len(classrooms) * random.randint(20, 30)
            
            # Generate random behavior scores for each class
            class_behavior_scores = {}
            for classroom in classrooms:
                class_behavior_scores[classroom['name']] = random.randint(75, 95)
            
            # Calculate average behavior score
            average_behavior_score = sum(class_behavior_scores.values()) // len(class_behavior_scores) if class_behavior_scores else 85
            
            # Generate example recent behaviors
            recent_behaviors = []
            student_names = [
                "Emma Thompson", "James Wilson", "Sophia Martinez", 
                "Ethan Brown", "Olivia Davis", "Noah Johnson"
            ]
            behavior_descriptions = [
                "Excellent participation in class discussion",
                "Disrupting class with excessive talking",
                "Helping classmate with difficult problem",
                "Outstanding homework submission",
                "Late to class without excuse",
                "Great teamwork during group project"
            ]
            
            for i in range(5):
                recent_behaviors.append({
                    'student': {'user': {'get_full_name': lambda i=i: student_names[i % len(student_names)]}},
                    'points': random.choice([5, 3, -2, 4, -3, 2]),
                    'description': behavior_descriptions[i % len(behavior_descriptions)],
                    'recorded_at': f"{random.randint(1, 12)}/{random.randint(1, 28)}/2025, {random.randint(8, 4)}:{random.randint(0, 59):02d} {'AM' if random.randint(0, 1) == 0 else 'PM'}"
                })
            
            # Generate students requiring attention
            students_requiring_attention = []
            for i in range(4):
                students_requiring_attention.append({
                    'id': i + 1,
                    'name': student_names[i % len(student_names)],
                    'class': list(class_behavior_scores.keys())[i % len(class_behavior_scores)] if class_behavior_scores else "Unknown",
                    'behavior_score': random.randint(65, 75),
                    'points': random.randint(-8, -3)
                })
            
            # Set pending assessments
            pending_assessments = random.randint(5, 15)
        
        # Prepare chart data
        chart_data = []
        for i, classroom in enumerate(classrooms):
            classroom_name = classroom['name'] if isinstance(classroom, dict) else classroom.name
            score = class_behavior_scores.get(classroom_name, 80)
            
            # Generate random data points for the chart
            data_points = []
            for j in range(10):  # 10 months
                # Add some variation to the score for each month
                variation = 1 if (j % 3 == 0) else (-1 if j % 3 == 1 else 0)
                data_points.append(score + variation)
            
            chart_data.append({
                'name': classroom_name,
                'data': data_points,
                'color': i + 1  # For get_color filter
            })
        
        # Prepare radar chart data
        radar_data = []
        for i, classroom in enumerate(classrooms):
            classroom_name = classroom['name'] if isinstance(classroom, dict) else classroom.name
            score = class_behavior_scores.get(classroom_name, 80)
            
            # Generate data for the 5 radar chart categories
            radar_points = [
                score,  # Behavior
                score + 5 + (2 if i % 2 == 0 else -2),  # Attendance
                score - 3 + (3 if i % 2 == 0 else -3),  # Participation
                score + 2 + (2 if i % 2 == 0 else -2),  # Homework
                score + 4 + (4 if i % 2 == 0 else -4)   # Test Scores
            ]
            
            radar_data.append({
                'name': classroom_name,
                'data': radar_points,
                'color': i + 1  # For get_color filter
            })
        
        context = {
            'teacher': teacher,
            'classrooms': classrooms,
            'total_students': total_students,
            'class_behavior_scores': class_behavior_scores,
            'average_behavior_score': average_behavior_score,
            'recent_behaviors': recent_behaviors,
            'students_requiring_attention': students_requiring_attention,
            'years_experience': int(teacher.years_experience) if hasattr(teacher, 'years_experience') and teacher.years_experience is not None else 0,
            'pending_assessments': pending_assessments,
            'chart_data': chart_data,
            'radar_data': radar_data
        }
        
    except Exception as e:
        logger.error(f"Error in teacher profile: {str(e)}")
        context = {'error': 'An error occurred while loading the teacher profile'}
    
    return render(request, "frontend/pages/ViewProfileTeacher/index.html", context)

@login_required
def student_profile(request):
    if not request.user.groups.filter(name="Student").exists():
        logger.warning(f"Unauthorized access attempt to student profile by {request.user.username}")
        return redirect('login')
    
    try:
        student = Student.objects.get(user=request.user)
        subjects = StudentSubject.objects.filter(student=student).select_related('subject')
        
        context = {
            'student': student,
            'subjects': subjects
        }
    except Student.DoesNotExist:
        logger.error(f"Student profile not found for user {request.user.username}")
        context = {'error': 'Student profile not found'}
    
    return render(request, "frontend/pages/ViewProfileStudent/index.html", context)


@login_required
@require_POST
def deduct_points(request):
    """Deduct points from a student."""
    try:
        # Get form data
        student_id = request.POST.get('student_id')
        points = int(request.POST.get('points', 0))  # This should be a negative number
        reason = request.POST.get('custom_reason', request.POST.get('reason', 'Unspecified'))
        
        # Ensure points is negative for deductions
        if points > 0:
            points = -points
        
        # Get the student and create behavior record
        student = Student.objects.get(id=student_id)
        
        # Get classroom/subject context if available
        classroom_id = request.POST.get('classroom_id')
        subject = None
        
        if classroom_id:
            try:
                classroom = ClassRoom.objects.get(id=classroom_id)
                subject = classroom.subject
            except ClassRoom.DoesNotExist:
                pass
        
        # Create the behavior record
        behavior = Behavior.objects.create(
            student=student,
            subject=subject,
            behavior_type='negative',
            description=reason,
            points=points,  # This should be negative
            recorded_by=request.user.get_full_name() or request.user.username
        )
        
        # Calculate total points for the student
        total_points = Behavior.objects.filter(student=student).aggregate(Sum('points'))['points__sum'] or 0
        
        return JsonResponse({
            'success': True,
            'message': f'Deducted {abs(points)} points from {student.user.get_full_name() or student.user.username}',
            'total_points': total_points
        })
    except Exception as e:
        logger.error(f"Error deducting points: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def teacher_settings(request):
    if not request.user.groups.filter(name__in=["Teacher", "Staff"]).exists():
        logger.warning(f"Unauthorized access attempt to teacher settings by {request.user.username}")
        return redirect('login')
    
    try:
        teacher, created = Teacher.objects.get_or_create(
            user=request.user,
            defaults={
                'department': 'General',
                'years_experience': 0,
                'office': 'Main Building',
                'office_hours': 'Mon-Fri: 9:00 AM - 5:00 PM',
                'phone': '555-123-4567'
            }
        )
        
        # Initialize forms
        profile_form = TeacherProfileForm(instance=teacher, user=request.user)
        notification_form = NotificationSettingsForm()
        display_form = DisplaySettingsForm()
        password_form = CustomPasswordChangeForm(request.user)
        
        if request.method == 'POST':
            form_type = request.POST.get('form_type')
            
            if form_type == 'profile':
                profile_form = TeacherProfileForm(request.POST, request.FILES, instance=teacher, user=request.user)
                if profile_form.is_valid():
                    # Update User model fields
                    user = request.user
                    user.first_name = profile_form.cleaned_data['first_name']
                    user.last_name = profile_form.cleaned_data['last_name']
                    user.email = profile_form.cleaned_data['email']
                    user.save()
                    
                    # Save Teacher model fields
                    profile_form.save()
                    
                    messages.success(request, "Your profile has been updated successfully!")
                    return redirect('teacher_settings')
                else:
                    messages.error(request, "Please correct the errors below.")
            
            elif form_type == 'notification':
                notification_form = NotificationSettingsForm(request.POST)
                if notification_form.is_valid():
                    # Save notification preferences to session or database
                    for key, value in notification_form.cleaned_data.items():
                        request.session[f'notification_{key}'] = value
                    
                    messages.success(request, "Your notification settings have been updated successfully!")
                    return redirect('teacher_settings')
                else:
                    messages.error(request, "Please correct the errors below.")
            
            elif form_type == 'display':
                display_form = DisplaySettingsForm(request.POST)
                if display_form.is_valid():
                    # Save display preferences to session or database
                    for key, value in display_form.cleaned_data.items():
                        request.session[f'display_{key}'] = value
                    
                    messages.success(request, "Your display settings have been updated successfully!")
                    return redirect('teacher_settings')
                else:
                    messages.error(request, "Please correct the errors below.")
            
            elif form_type == 'password':
                password_form = CustomPasswordChangeForm(request.user, request.POST)
                if password_form.is_valid():
                    user = password_form.save()
                    # Update the session to prevent the user from being logged out
                    update_session_auth_hash(request, user)
                    
                    messages.success(request, "Your password has been changed successfully!")
                    return redirect('teacher_settings')
                else:
                    messages.error(request, "Please correct the errors below.")
        
        # Load saved notification preferences from session
        if not notification_form.is_bound:
            initial_notification = {}
            for field in notification_form.fields:
                initial_notification[field] = request.session.get(f'notification_{field}', True)
            notification_form = NotificationSettingsForm(initial=initial_notification)
        
        # Load saved display preferences from session
        if not display_form.is_bound:
            initial_display = {}
            for field in display_form.fields:
                if field in ['theme', 'dashboard_layout']:
                    initial_display[field] = request.session.get(f'display_{field}', 
                                                              'light' if field == 'theme' else 'default')
                else:
                    initial_display[field] = request.session.get(f'display_{field}', True)
            display_form = DisplaySettingsForm(initial=initial_display)
        
        context = {
            'profile_form': profile_form,
            'notification_form': notification_form,
            'display_form': display_form,
            'password_form': password_form,
            'teacher': teacher,
            'active_tab': request.GET.get('tab', 'profile')
        }
        
        return render(request, "frontend/pages/SettingPageTeacher/index.html")
    
    except Exception as e:
        logger.error(f"Error in teacher settings: {str(e)}")
        messages.error(request, f"An error occurred while loading settings: {str(e)}")
        return redirect('teacher_profile')

@login_required
def teacher_faq(request):
    if not request.user.groups.filter(name__in=["Teacher", "Staff"]).exists():
        logger.warning(f"Unauthorized access attempt to teacher FAQ by {request.user.username}")
        return redirect('login')
    return render(request, "frontend/pages/FAQsTeacher/index.html")

@login_required
def student_dash(request):
    if not request.user.groups.filter(name="Student").exists():
        logger.warning(f"Unauthorized access attempt to student dashboard by {request.user.username}")
        return redirect('login')
    
    try:
        student = Student.objects.get(user=request.user)
        subjects = StudentSubject.objects.filter(student=student).select_related('subject')
        
        # Calculate average grade
        total_grade = 0
        count = 0
        for subject in subjects:
            if subject.grade:
                total_grade += subject.grade
                count += 1
        
        average_grade = round(total_grade / count, 1) if count > 0 else None
        
        context = {
            'student': student,
            'subjects': subjects,
            'average_grade': average_grade
        }
    except Student.DoesNotExist:
        logger.error(f"Student profile not found for user {request.user.username}")
        context = {'error': 'Student profile not found'}
    
    return render(request, "frontend/pages/StudentDashboard/index.html", context)

@login_required
def student_settings(request):
    if not request.user.groups.filter(name="Student").exists():
        logger.warning(f"Unauthorized access attempt to student settings by {request.user.username}")
        return redirect('login')
    
    # Get or create student record
    student, created = Student.objects.get_or_create(user=request.user)
    
    # Show different message if this is a new student record
    is_new_profile = created or not any([
        student.date_of_birth, 
        student.address, 
        student.emergency_contact_name,
        student.emergency_phone
    ])
    
    # Calculate profile completion percentage
    profile_fields = [
        request.user.first_name,
        request.user.last_name,
        request.user.email,
        student.date_of_birth,
        student.address,
        student.emergency_contact_name,
        student.emergency_contact_relation,
        student.emergency_phone
    ]
    
    filled_fields = sum(1 for field in profile_fields if field)
    profile_completion = int((filled_fields / len(profile_fields)) * 100)
    
    context = {
        'student': student,
        'is_new_profile': is_new_profile,
        'profile_completion': profile_completion
    }
    
    # Handle form submissions
    if request.method == "POST":
        form_type = request.POST.get('form_type', '')
        
        # Handle personal information update
        if form_type == 'personal_info':
            request.user.first_name = request.POST.get('firstName', '').strip()
            request.user.last_name = request.POST.get('lastName', '').strip()
            request.user.email = request.POST.get('email', '').strip()
            request.user.save()
            
            # Update student fields
            student.date_of_birth = request.POST.get('dateOfBirth') or student.date_of_birth
            student.address = request.POST.get('address', '').strip()
            student.save()
            
            messages.success(request, "Personal information updated successfully!")
            
        # Handle emergency contact update
        elif form_type == 'emergency_contact':
            student.emergency_contact_name = request.POST.get('emergencyName', '').strip()
            student.emergency_contact_relation = request.POST.get('emergencyRelation', '').strip()
            student.emergency_phone = request.POST.get('emergencyPhone', '').strip()
            student.alt_contact_name = request.POST.get('altName', '').strip()
            student.alt_contact_relation = request.POST.get('altRelation', '').strip() 
            student.alt_contact_phone = request.POST.get('altPhone', '').strip()
            student.save()
            
            messages.success(request, "Emergency contacts updated successfully!")
            
        # Handle password change
        elif form_type == 'change_password':
            current_password = request.POST.get('currentPassword')
            new_password = request.POST.get('newPassword')
            confirm_password = request.POST.get('confirmPassword')
            
            # Validate current password
            if not request.user.check_password(current_password):
                messages.error(request, "Current password is incorrect.")
                return render(request, "frontend/pages/SettingPageStudent/index.html", context)
                
            # Validate new password
            if new_password != confirm_password:
                messages.error(request, "New passwords don't match.")
                return render(request, "frontend/pages/SettingPageStudent/index.html", context)
                
            if len(new_password) < 8:
                messages.error(request, "Password must be at least 8 characters long.")
                return render(request, "frontend/pages/SettingPageStudent/index.html", context)
                
            # Change password
            request.user.set_password(new_password)
            request.user.save()
            
            # Re-authenticate to prevent logout
            user = authenticate(username=request.user.username, password=new_password)
            if user:
                login(request, user)
                
            messages.success(request, "Password changed successfully!")
            
        # Handle notification preferences
        elif form_type == 'notifications':
            # Just acknowledge the form submission without trying to save to non-existent fields
            messages.success(request, "Notification preferences saved!")
            
        # Handle appearance settings
        elif form_type == 'appearance':
            # Just acknowledge the form submission without trying to save to non-existent fields
            messages.success(request, "Display settings saved!")
            
        # Handle privacy settings
        elif form_type == 'privacy':
            # Just acknowledge the form submission without trying to save to non-existent fields
            messages.success(request, "Privacy settings saved!")
    
    return render(request, "frontend/pages/SettingPageStudent/index.html", context)

@login_required
def student_behavior_history(request):
    """
    View for student behavior history page
    """
    if not request.user.groups.filter(name="Student").exists():
        logger.warning(f"Unauthorized access attempt to behavior history by {request.user.username}")
        return redirect('login')
    
    try:
        student = Student.objects.get(user=request.user)
        
        # Get filter parameters
        subject_id = request.GET.get('subject', 'all')
        behavior_type = request.GET.get('type', 'all')
        date_from = request.GET.get('from', '')
        date_to = request.GET.get('to', '')
        
        # Base query
        behaviors_query = Behavior.objects.filter(student=student).select_related('subject').order_by('-recorded_at')
        
        # Apply filters
        if subject_id != 'all' and subject_id.isdigit():
            behaviors_query = behaviors_query.filter(subject_id=int(subject_id))
            
        if behavior_type != 'all':
            behaviors_query = behaviors_query.filter(behavior_type=behavior_type)
            
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                behaviors_query = behaviors_query.filter(recorded_at__gte=date_from_obj)
            except ValueError:
                logger.warning(f"Invalid date format for date_from: {date_from}")
                
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
                # Add one day to include the end date
                date_to_obj = date_to_obj + timedelta(days=1)
                behaviors_query = behaviors_query.filter(recorded_at__lt=date_to_obj)
            except ValueError:
                logger.warning(f"Invalid date format for date_to: {date_to}")
        
        # Paginate results
        paginator = Paginator(behaviors_query, 10)  # 10 records per page
        page_number = request.GET.get('page', 1)
        behaviors = paginator.get_page(page_number)
        
        # Get statistics
        total_points = Behavior.objects.filter(student=student).aggregate(total=Sum('points'))['total'] or 0
        positive_count = Behavior.objects.filter(student=student, behavior_type='positive').count()
        negative_count = Behavior.objects.filter(student=student, behavior_type='negative').count()
        
        # Get subjects for filter dropdown
        subjects = Subject.objects.all()
        
        # Get chart data (last 6 months)
        six_months_ago = datetime.now() - timedelta(days=180)
        chart_data = []
        
        # Prepare chart data by month
        for i in range(6):
            month_start = six_months_ago + timedelta(days=30 * i)
            month_end = six_months_ago + timedelta(days=30 * (i + 1))
            
            month_positive = Behavior.objects.filter(
                student=student,
                behavior_type='positive',
                recorded_at__gte=month_start,
                recorded_at__lt=month_end
            ).aggregate(total=Sum('points'))['total'] or 0
            
            month_negative = abs(Behavior.objects.filter(
                student=student,
                behavior_type='negative',
                recorded_at__gte=month_start,
                recorded_at__lt=month_end
            ).aggregate(total=Sum('points'))['total'] or 0)
            
            month_net = month_positive - month_negative
            
            chart_data.append({
                'month': month_start.strftime('%b'),
                'positive': month_positive,
                'negative': month_negative,
                'net': month_net
            })
        
        # Calculate class rank based on total points
        all_students = Student.objects.annotate(
            total_points=Sum('behaviors__points')
        ).order_by('-total_points')
        
        # Find current student's rank
        rank = 1
        for s in all_students:
            if s.id == student.id:
                break
            rank += 1
        
        context = {
            'student': student,
            'behaviors': behaviors,
            'subjects': subjects,
            'total_points': total_points,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'rank': rank,
            'chart_data': json.dumps(chart_data),
            'selected_subject': subject_id,
            'selected_type': behavior_type,
            'date_from': date_from,
            'date_to': date_to
        }
        
    except Student.DoesNotExist:
        logger.error(f"Student profile not found for user {request.user.username}")
        context = {'error': 'Student profile not found'}
    
    return render(request, "frontend/pages/BehaviorHistory/index.html", context)


@login_required
@require_POST
def unassign_student(request):
    """Unassign a student from their seat."""
    try:
        data = json.loads(request.body)
        student_id = data.get('student_id')
        seating_plan_id = data.get('seating_plan_id')
        
        # Get the student and seating plan
        student = Student.objects.get(id=student_id)
        seating_plan = SeatingPlan.objects.get(id=seating_plan_id)
        
        # Find and delete the seat assignment
        seat_assignment = SeatAssignment.objects.filter(
            seating_plan=seating_plan,
            student=student
        ).first()
        
        if not seat_assignment:
            return JsonResponse({
                'success': False,
                'error': 'Student is not assigned to any seat'
            })
        
        # Delete the assignment
        seat_assignment.delete()
        
        # Get student's behavior category for UI update
        behaviors = Behavior.objects.filter(student=student)
        total_points = sum(b.points for b in behaviors)
        
        # Calculate thresholds (similar to seating_plan view)
        # Fix: Use the correct related name 'subjects' instead of 'studentsubject'
        all_students = Student.objects.filter(
            subjects__subject=seating_plan.classroom.subject
        ).distinct()
        
        all_points = []
        for s in all_students:
            s_behaviors = Behavior.objects.filter(student=s)
            s_points = sum(b.points for b in s_behaviors)
            all_points.append(s_points)
        
        all_points.sort(reverse=True)
        total_students = len(all_points)
        
        # Top 50%
        green_threshold = all_points[int(total_students * 0.5) - 1] if total_students > 1 else 0
        
        # Next 25%
        orange_threshold = all_points[int(total_students * 0.75) - 1] if total_students > 3 else 0
        
        # Determine category
        if total_points >= green_threshold:
            category = 'green-category'
        elif total_points >= orange_threshold:
            category = 'orange-category'
        else:
            category = 'red-category'
        
        return JsonResponse({
            'success': True,
            'message': f'Unassigned {student.user.get_full_name() or student.user.username} from their seat',
            'category': category
        })
    except Exception as e:
        logger.error(f"Error unassigning student: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def get_client_ip(request):
    """Get the client's IP address from the request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
