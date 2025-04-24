from django.urls import path
from .views import (
    login_view, seating_plan, behaviour_history, logout_view, 
    teacher_profile, student_profile, teacher_settings, 
    student_dash, student_settings, login_faq, teacher_faq,
    student_behavior_history,
    # Make sure these are imported
    award_points, deduct_points, update_seat_assignment,
    get_student_profile, randomize_seating, save_seating_plan,
    unassign_student  # Add this new import
)

urlpatterns = [
    path('', login_view, name='login'),
    path('teacher-profile/', teacher_profile, name='teacher_profile'),
    path('student-profile/', student_profile, name='student_profile'),
    path('seating-plan/', seating_plan, name='seatingPlan'),
    path('behavior-history/', student_behavior_history, name='student_behavior_history'),
    path('logout/', logout_view, name='logout'),
    path('teacher-settings/', teacher_settings, name='teacher_settings'),
    path('student-dash/', student_dash, name='student_dash'),
    path('student-settings/', student_settings, name='student_settings'),
    path('login-faq/', login_faq, name='login_faq'),
    path('teacher-faq/', teacher_faq, name='teacher_faq'),
    
    # Make sure these URL patterns exist
    path('award-points/', award_points, name='award_points'),
    path('deduct-points/', deduct_points, name='deduct_points'),
    path('update-seat-assignment/', update_seat_assignment, name='update_seat_assignment'),
    path('get-student-profile/', get_student_profile, name='get_student_profile'),
    path('randomize-seating/', randomize_seating, name='randomize_seating'),
    path('save-seating-plan/', save_seating_plan, name='save_seating_plan'),
    path('unassign-student/', unassign_student, name='unassign_student'),  # Add this new URL pattern
]
