from django.contrib import admin
from .models import BehaviorPoint

@admin.register(BehaviorPoint)
class BehaviorPointAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'student', 'teacher', 'points', 'reason', 'classroom')
    list_filter = ('points', 'classroom', 'timestamp')
    search_fields = ('student__username', 'reason', 'classroom')
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('student', 'teacher')
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.teacher = request.user
        super().save_model(request, obj, form, change)
    
    def get_fields(self, request, obj=None):
        fields = list(super().get_fields(request, obj))
        if 'teacher' in fields:
            fields.remove('teacher')
        return fields
