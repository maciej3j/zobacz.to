from django import forms
from .models import UserProfile
from .models import Event, EventComment, Announcement
from django.contrib.auth.models import User

class PersonalDataForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
from .models import Event, EventComment, Announcement, ContactMessage

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'date', 'location']
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class EventCommentForm(forms.ModelForm):
    class Meta:
        model = EventComment
        fields = ['comment', 'rating']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3}),
            'rating': forms.Select(choices=[(i, i) for i in range(1, 6)]),
        }

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'category']

class AcademicDataForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['university', 'faculty', 'field_of_study', 'study_year', 'main_discipline', 'interests']
class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4}),
        }

class ContactAnswerForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['answer']
        widgets = {
            'answer': forms.Textarea(attrs={'rows': 2}),
        }
