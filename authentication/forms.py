from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from .models import Teacher



class TeacherProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    
    class Meta:
        model = Teacher
        fields = ['department', 'years_experience', 'office', 'office_hours', 'phone']
        widgets = {
            'office_hours': forms.TextInput(attrs={'placeholder': 'e.g., Mon-Fri: 9:00 AM - 5:00 PM'}),
            'phone': forms.TextInput(attrs={'placeholder': 'e.g., 555-123-4567'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(TeacherProfileForm, self).__init__(*args, **kwargs)
        
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
        
        # Add Bootstrap classes to all form fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            if field_name != 'profile_picture':
                field.widget.attrs['class'] = 'form-control'

class NotificationSettingsForm(forms.Form):
    email_notifications = forms.BooleanField(required=False, initial=True, 
                                           label="Email Notifications",
                                           help_text="Receive email notifications for important updates")
    
    behavior_alerts = forms.BooleanField(required=False, initial=True,
                                       label="Behavior Alerts", 
                                       help_text="Get alerts when student behavior scores change significantly")
    
    assignment_reminders = forms.BooleanField(required=False, initial=True,
                                            label="Assignment Reminders",
                                            help_text="Receive reminders about upcoming assignment deadlines")
    
    staff_announcements = forms.BooleanField(required=False, initial=True,
                                           label="Staff Announcements",
                                           help_text="Get notifications about staff meetings and announcements")
    
    parent_messages = forms.BooleanField(required=False, initial=True,
                                       label="Parent Messages",
                                       help_text="Be notified when parents send messages")
    
    def __init__(self, *args, **kwargs):
        super(NotificationSettingsForm, self).__init__(*args, **kwargs)
        # Add Bootstrap classes to all form fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-check-input'

class DisplaySettingsForm(forms.Form):
    THEME_CHOICES = [
        ('light', 'Light Mode'),
        ('dark', 'Dark Mode'),
        ('system', 'Use System Setting')
    ]
    
    DASHBOARD_LAYOUT_CHOICES = [
        ('default', 'Default Layout'),
        ('compact', 'Compact Layout'),
        ('expanded', 'Expanded Layout')
    ]
    
    theme = forms.ChoiceField(choices=THEME_CHOICES, initial='light', 
                            label="Theme",
                            widget=forms.RadioSelect)
    
    dashboard_layout = forms.ChoiceField(choices=DASHBOARD_LAYOUT_CHOICES, initial='default',
                                       label="Dashboard Layout",
                                       widget=forms.RadioSelect)
    
    show_behavior_chart = forms.BooleanField(required=False, initial=True,
                                           label="Show Behavior Chart",
                                           help_text="Display behavior charts on your dashboard")
    
    show_calendar = forms.BooleanField(required=False, initial=True,
                                     label="Show Calendar",
                                     help_text="Display calendar on your dashboard")
    
    def __init__(self, *args, **kwargs):
        super(DisplaySettingsForm, self).__init__(*args, **kwargs)
        # Add Bootstrap classes to radio buttons
        self.fields['theme'].widget.attrs['class'] = 'form-check-input'
        self.fields['dashboard_layout'].widget.attrs['class'] = 'form-check-input'
        # Add Bootstrap classes to checkboxes
        self.fields['show_behavior_chart'].widget.attrs['class'] = 'form-check-input'
        self.fields['show_calendar'].widget.attrs['class'] = 'form-check-input'

class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super(CustomPasswordChangeForm, self).__init__(*args, **kwargs)
        # Add Bootstrap classes to all form fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
