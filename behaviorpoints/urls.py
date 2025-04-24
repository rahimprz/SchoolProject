from django.urls import path
from . import views

urlpatterns = [
    path('award/', views.award_point, name='award_point'),
] 