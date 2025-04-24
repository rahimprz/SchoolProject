from django.db import models
from django.contrib.auth.models import User

class BehaviorPoint(models.Model):
    student = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='received_points',
        limit_choices_to={'groups__name': 'Student'}
    )
    teacher = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='given_points',
        editable=False
    )
    points = models.IntegerField()
    reason = models.CharField(max_length=255)
    classroom = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        permissions = [
            ("can_award_points", "Can award behavior points"),
        ]
