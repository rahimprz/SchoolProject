from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_http_methods
import json
from .models import BehaviorPoint

# Create your views here.

@login_required
@permission_required('behaviorpoints.can_award_points')
@require_http_methods(["POST"])
def award_point(request):
    data = json.loads(request.body)
    point = BehaviorPoint.objects.create(
        student_id=data['student_id'],
        teacher=request.user,
        points=data['points'],  # should be +1 or -1 but will add better constraint here
        reason=data['reason'],
        classroom=data['classroom']
    )
    return JsonResponse({'status': 'success'})

@login_required
def graphDataset(request):
    students = users.objects.filter(behaviourpoints__isnull=False).distinct()
    data = []
    for student in students:
        posPoints = BehaviorPoint.objects.filter(student=student, points__gt=0).aggregate(TOTAL = Sum('points'))['total']
        negPoints = BehaviorPoint.objects.filter('points' < 0).aggregate(TOTAL = Sum('points'))['total']
        data.append({
            'student': student.username,
            'positive': posPoints,
            'negative': negPoints,
            'net': posPoints - negPoints,
        })
    
    context = {
        'graphData': json.dumps(data)
    }
    return render(request, 'index.html', data)
