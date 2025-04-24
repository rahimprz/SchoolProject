### @Author: LordWasteds
### @Date: 03-02-2026
### @Description: This file contains signals for the backend app.

from django.contrib.auth.models import Group
from django.db.models.signals import post_migrate
from django.dispatch import receiver

@receiver(post_migrate)
def create_user_groups(sender, **kwargs):
    """ Init default user groups when migrations are applied """
    groups = ["Student", "Teacher", "Staff"]
    for group in groups:
        Group.objects.get_or_create(name=group)
    print("User groups created/updated")
