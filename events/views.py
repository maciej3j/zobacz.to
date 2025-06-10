from django.shortcuts import render, redirect
from django.views.generic import ListView
from .models import Event
from .forms import EventForm, EventCommentForm, AnnouncementForm
from .models import EventEnrollment, EventComment, Announcement
from django.db.models import Avg, Count
from django.utils.timezone import now
from django.utils import timezone
from .decorators import organizer_required, admin_required
from .decorators import student_required
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django import forms
from .forms import PersonalDataForm, AcademicDataForm # Upewnij się, że AcademicDataForm zawiera 'interests'
from .models import FAQ, ContactMessage, Event
from .forms import ContactForm, ContactAnswerForm
from django.http import HttpResponseForbidden
from django.http import JsonResponse
from django.template.loader import render_to_string
from events.models import UserProfile, ContactMessage
from accounts.models import OrganizerRequest

class EventListView(ListView):
    model = Event
    template_name = "events/events_list.html"
    context_object_name = "events"

    def get_queryset(self):
        queryset = Event.objects.filter(date__gte=now()).order_by("date")  # tylko przyszłe wydarzenia
        sort = self.request.GET.get("sort")
        location = self.request.GET.get("location")

        if location:
            queryset = queryset.filter(location__icontains=location)

        if sort == "date_desc":
            queryset = queryset.order_by("-date")
        elif sort == "title":
            queryset = queryset.order_by("title")

        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated:
            user_enrollments = EventEnrollment.objects.filter(user=user).values_list('event_id', flat=True)
            context['user_enrollments'] = set(user_enrollments)
            is_organizer = user.groups.filter(name='organizer').exists()
            context['is_organizer'] = is_organizer
            if is_organizer:
                organized_events = (
                    Event.objects.filter(created_by=user)
                    .annotate(
                        participants_count=Count('eventenrollment', distinct=True),
                        comments_count=Count('comments', distinct=True),
                        avg_rating=Avg('comments__rating')
                    )
                    .order_by('date')
                )
                context['organized_events'] = organized_events
        else:
            context['user_enrollments'] = set()
            context['is_organizer'] = False

        if user.is_authenticated and user.groups.filter(name="admin").exists():
            context['organizer_requests_count'] = OrganizerRequest.objects.filter(is_reviewed=False).count()
            context['messages_count'] = ContactMessage.objects.filter(answer__isnull=True).count()

        return context

@organizer_required
def add_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)  # dodaj request.FILES
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()
            messages.success(request, "Wydarzenie zostało dodane pomyślnie!")
            return redirect('events_list')
    else:
        form = EventForm()
    return render(request, 'events/add_event.html', {'form': form})

@organizer_required
def edit_event(request, event_id):
    event = get_object_or_404(Event, id=event_id, created_by=request.user)
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, "Wydarzenie zostało zaktualizowane!")
            return redirect('events_list')
    else:
        form = EventForm(instance=event)
    return render(request, 'events/add_event.html', {'form': form, 'edit_mode': True, 'event': event})

@login_required
def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    is_admin = request.user.groups.filter(name="admin").exists()
    is_owner = event.created_by == request.user
    if is_admin or is_owner:
        event.delete()
        messages.success(request, "Wydarzenie zostało usunięte.")
    else:
        messages.error(request, "Nie masz uprawnień do usunięcia tego wydarzenia.")
    return redirect('events_list')

@student_required
def enroll_in_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if event.eventenrollment_set.filter(user=request.user).exists():
        messages.info(request, "Jesteś już zapisany na to wydarzenie.")
    else:
        event.eventenrollment_set.create(user=request.user)
        messages.success(request, "Pomyślnie zapisano na wydarzenie!")

    return redirect('events_list')

@student_required
def unenroll_from_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    enrollment = event.eventenrollment_set.filter(user=request.user).first()
    if enrollment:
        enrollment.delete()
        messages.success(request, "Zrezygnowano z udziału w wydarzeniu.")
    else:
        messages.info(request, "Nie jesteś zapisany na to wydarzenie.")
    return redirect('event_detail', event_id=event.id)

@login_required
def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    comments = event.comments.select_related('user').order_by('-created_at')
    avg_rating = event.comments.aggregate(avg=Avg('rating'))['avg']  
    if request.method == 'POST':
        form = EventCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.event = event
            comment.user = request.user
            comment.save()
            messages.success(request, "Twój komentarz został dodany.")
            return redirect('event_detail', event_id=event.id)
    else:
        form = EventCommentForm()
        return render(request, 'events/event_detail.html', {
        'event': event,
        'comments': comments,
        'form': form,
        'avg_rating': round(avg_rating or 0, 2),  
    })

@login_required
def home(request):
    announcements = Announcement.objects.order_by('-created_at')[:5]
    admin_answers = []
    enrolled_events = [] # Initialize
    organizer_events = [] # Initialize
    is_student = False # Initialize boolean flags
    is_organizer = False
    is_admin = False # Initialize is_admin flag
    show_admin_answer = False

    if request.user.is_authenticated:
        is_student = request.user.groups.filter(name='student').exists()
        is_organizer = request.user.groups.filter(name='organizer').exists()
        is_admin = request.user.groups.filter(name='admin').exists() # Set is_admin flag

        if is_student or is_organizer: # Only fetch answers if user is student or organizer
            admin_answers = ContactMessage.objects.filter(
                user=request.user,
                answer__isnull=False
            ).order_by('-created_at')

        if is_student:
            enrolled_events = Event.objects.filter(eventenrollment__user=request.user).order_by('date')
        
        if is_organizer:
            organizer_events = (
                Event.objects.filter(created_by=request.user)
                .annotate(
                    participants_count=Count('eventenrollment', distinct=True),
                    comments_count=Count('comments', distinct=True),
                    avg_rating=Avg('comments__rating')
                )
                .order_by('date') # Added ordering for consistency
            )

        # Sprawdź, czy jest nowa odpowiedź i czy nie została już "przeczytana"
        show_admin_answer = bool(admin_answers) and (is_student or is_organizer)

    organizer_requests_count = OrganizerRequest.objects.filter(is_reviewed=False).count()
    messages_count = ContactMessage.objects.filter(answer__isnull=True).count()

    context = {
        'announcements': announcements,
        'admin_answers': admin_answers,
        'enrolled_events': enrolled_events, # Always pass
        'organizer_events': organizer_events, # Always pass
        'is_student': is_student, # Always pass boolean flags for template logic
        'is_organizer': is_organizer, # Always pass boolean flags for template logic
        'is_admin': is_admin, # Pass the new is_admin flag
        "show_admin_answer": show_admin_answer,
        "organizer_requests_count": organizer_requests_count,
        "messages_count": messages_count,
    }
    return render(request, 'home.html', context)

@admin_required
def add_announcement(request):
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.author = request.user
            announcement.save()
            messages.success(request, "Ogłoszenie zostało dodane pomyślnie!")
            return redirect('home')
    else:
        form = AnnouncementForm()
    return render(request, 'add_announcement.html', {'form': form})

@admin_required
def delete_announcement(request, announcement_id):
    announcement = get_object_or_404(Announcement, id=announcement_id)
    announcement.delete()
    messages.success(request, "Ogłoszenie zostało usunięte.")
    return redirect('home')


@login_required
def contact(request):
    user = request.user
    faqs = FAQ.objects.all()[:5]
    upcoming_events = Event.objects.filter(date__gte=timezone.now()).order_by('date')[:5]
    contact_info = {
        'email': 'info@zobacz.to',
        'phone': '+48 123 456 789',
        'address': 'ul. Akademicka 1, 90-001 Łódź',
    }

    admin_answers = ContactMessage.objects.filter(
        user=user,
        answer__isnull=False
    ).order_by('-created_at')
    is_student = user.groups.filter(name='student').exists()
    is_organizer = user.groups.filter(name='organizer').exists()
    is_admin = user.groups.filter(name='admin').exists() # Added for consistency

    if is_student or is_organizer:
        if request.method == 'POST':
            form = ContactForm(request.POST)
            if form.is_valid():
                contact_message = form.save(commit=False)
                contact_message.user = user
                contact_message.save()
                messages.success(request, "Twoja wiadomość została wysłana do administratora.")
                return redirect('contact')
        else:
            initial = {
                'name': f"{user.first_name} {user.last_name}".strip() or user.username,
                'email': user.email,
            }
            form = ContactForm(initial=initial)
            form.fields['name'].widget.attrs['readonly'] = True
            form.fields['email'].widget.attrs['readonly'] = True
        return render(request, 'contact.html', {
            'form': form,
            'faqs': faqs,
            'upcoming_events': upcoming_events,
            'contact_info': contact_info,
            'admin_answers': admin_answers,
            'is_student': is_student,
            'is_organizer': is_organizer,
            'is_admin': is_admin, # Pass to contact template
        })

    elif user.groups.filter(name='admin').exists():
        messages_list = ContactMessage.objects.all().order_by('-created_at')
        if request.method == 'POST' and 'answer_message_id' in request.POST:
            msg = ContactMessage.objects.get(id=request.POST['answer_message_id'])
            msg.answer = request.POST.get('answer', '')
            msg.is_answered = True
            msg.save()
            messages.success(request, "Odpowiedź została wysłana do użytkownika.")
            return redirect('contact')
        return render(request, 'contact_admin.html', {
            'messages_list': messages_list,
            'faqs': faqs,
            'contact_info': contact_info,
            'is_admin': is_admin, # Pass to contact_admin template
        })
    else: # For users not in student, organizer, or admin groups
        messages.error(request, "Nie masz uprawnień, aby wysyłać wiadomości lub przeglądać tę stronę.")
        return redirect('home') # Redirect to home or login page

@login_required
def profile(request):
    user = request.user

    try:
        profile = user.userprofile
    except AttributeError:
        # Handle case where user might not have a profile, e.g., create it.
        # This is a placeholder, you might have specific logic in accounts app
        profile = UserProfile.objects.create(user=user)

    enrolled_events = [] # Initialize
    organized_events = [] # Initialize
    is_student = user.groups.filter(name='student').exists()
    is_organizer = user.groups.filter(name='organizer').exists()
    is_admin = user.groups.filter(name='admin').exists() # Set is_admin flag

    if request.method == 'POST':
        # Handle personal data form submission
        if 'save_personal' in request.POST:
            personal_form = PersonalDataForm(request.POST, instance=user)
            if personal_form.is_valid():
                personal_form.save()
                messages.success(request, "Dane osobowe zostały zaktualizowane.")
                return redirect('profile')
            else:
                messages.error(request, "Błąd podczas aktualizacji danych osobowych.")
        
        # Handle academic and interests data form submission
        elif 'save_academic' in request.POST:
            academic_form = AcademicDataForm(request.POST, instance=profile)
            if academic_form.is_valid():
                academic_form.save()
                messages.success(request, "Dane akademickie i zainteresowania zostały zaktualizowane.")
            else:
                messages.error(request, "Błąd podczas aktualizacji danych akademickich i zainteresowań.")
        
        # After saving, re-fetch data to ensure updated context
        # This part ensures that after a POST, the page re-renders with correct data
        if is_student:
            enrolled_events = Event.objects.filter(eventenrollment__user=user).order_by('date')
        if is_organizer:
            organized_events = (
                Event.objects.filter(created_by=user)
                .annotate(
                    participants_count=Count('eventenrollment', distinct=True),
                    comments_count=Count('comments', distinct=True),
                    avg_rating=Avg('comments__rating')
                )
                .order_by('date')
            )
        
        # Re-initialize forms for the next render (after POST)
        personal_form = PersonalDataForm(instance=user)
        academic_form = AcademicDataForm(instance=profile)

        return render(request, 'profile.html', {
            'personal_form': personal_form,
            'academic_form': academic_form,
            'enrolled_events': enrolled_events, # Always pass
            'organized_events': organized_events, # Always pass
            'is_student': is_student, # Always pass boolean flags for template logic
            'is_organizer': is_organizer, # Always pass boolean flags for template logic
            'is_admin': is_admin, # Pass the new is_admin flag
        })

    # For GET requests, initialize forms with current instance data
    personal_form = PersonalDataForm(instance=user)
    academic_form = AcademicDataForm(instance=profile)

    # Populate enrolled_events if user is a student for GET requests
    if is_student:
        enrolled_events = Event.objects.filter(eventenrollment__user=user).order_by('date')
    
    # Populate organized_events if user is an organizer for GET requests
    if is_organizer:
        organized_events = (
            Event.objects.filter(created_by=user)
            .annotate(
                participants_count=Count('eventenrollment', distinct=True),
                comments_count=Count('comments', distinct=True),
                avg_rating=Avg('comments__rating')
            )
            .order_by('date')
        )

    context = {
        'personal_form': personal_form,
        'academic_form': academic_form,
        'enrolled_events': enrolled_events, # Always pass
        'organized_events': organized_events, # Always pass
        'is_student': is_student, # Always pass boolean flags for template logic
        'is_organizer': is_organizer, # Always pass boolean flags for template logic
        'is_admin': is_admin, # Pass the new is_admin flag
    }

    if request.user.is_authenticated and request.user.groups.filter(name="admin").exists():
        context['organizer_requests_count'] = OrganizerRequest.objects.filter(is_reviewed=False).count()
        context['messages_count'] = ContactMessage.objects.filter(answer__isnull=True).count()

    return render(request, 'profile.html', context)

@login_required
def event_participants_ajax(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    # Tylko organizator-właściciel lub admin może zobaczyć uczestników
    if event.created_by != request.user and not request.user.groups.filter(name="admin").exists():
        return JsonResponse({'error': 'Brak uprawnień'}, status=403)
    enrollments = EventEnrollment.objects.filter(event=event).select_related('user')
    html = render_to_string('events/participants_list_fragment.html', {'enrollments': enrollments, 'event': event}, request=request)
    return JsonResponse({'html': html})

@login_required
def mark_admin_answer_seen(request):
    if request.method == "POST":
        request.user.profile.admin_answer_seen = True
        request.user.profile.save()
        return JsonResponse({"status": "ok"})
    return JsonResponse({"status": "error"}, status=400)

@login_required
@user_passes_test(lambda u: u.groups.filter(name="admin").exists())
def delete_comment(request, comment_id):
    comment = get_object_or_404(EventComment, id=comment_id)
    event_id = comment.event.id
    comment.delete()
    return redirect('event_detail', event_id)
