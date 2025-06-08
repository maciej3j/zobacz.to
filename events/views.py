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
from django.contrib.auth.decorators import login_required
from django import forms
from .forms import PersonalDataForm, AcademicDataForm
from .models import FAQ, ContactMessage, Event
from .forms import ContactForm, ContactAnswerForm
from django.http import HttpResponseForbidden
from django.http import JsonResponse
from django.template.loader import render_to_string

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
        if self.request.user.is_authenticated:
            user_enrollments = EventEnrollment.objects.filter(user=self.request.user).values_list('event_id', flat=True)
            context['user_enrollments'] = set(user_enrollments)
        else:
            context['user_enrollments'] = set()
        return context

@organizer_required
def add_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()
            return redirect('events_list')
    else:
        form = EventForm()
    return render(request, 'events/add_event.html', {'form': form})

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
    if request.user.groups.filter(name__in=['student', 'organizer']).exists():
        admin_answers = ContactMessage.objects.filter(
            user=request.user,
            answer__isnull=False
        ).order_by('-created_at')

    if request.user.groups.filter(name='student').exists():
        enrolled_events = Event.objects.filter(eventenrollment__user=request.user).order_by('date')
        context = {
            'enrolled_events': enrolled_events,
            'is_student': True,
            'announcements': announcements,
            'admin_answers': admin_answers,
        }
        return render(request, 'home.html', context)

    elif request.user.groups.filter(name='organizer').exists():
        events = Event.objects.filter(created_by=request.user)
        event_stats = []

        for event in events:
            enrollment_count = EventEnrollment.objects.filter(event=event).count()
            comment_count = EventComment.objects.filter(event=event).count()
            avg_rating = EventComment.objects.filter(event=event).aggregate(avg=Avg('rating'))['avg']

            event_stats.append({
                'event': event,
                'enrollment_count': enrollment_count,
                'comment_count': comment_count,
                'avg_rating': round(avg_rating or 0, 2)
            })

        organizer_events = (
            Event.objects.filter(created_by=request.user)
            .annotate(
                participants_count=Count('eventenrollment', distinct=True),
                comments_count=Count('comments', distinct=True),
                avg_rating=Avg('comments__rating')
            )
        )

        context = {
            'event_stats': event_stats,
            'is_organizer': True,
            'announcements': announcements,
            'organizer_events': organizer_events,
            'admin_answers': admin_answers,
        }
        return render(request, 'home.html', context)

    else:
        context = {
            'announcements': announcements,
            'admin_answers': admin_answers,
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
            return redirect('home')
    else:
        form = AnnouncementForm()
    return render(request, 'add_announcement.html', {'form': form})

@admin_required
def delete_announcement(request, announcement_id):
    announcement = get_object_or_404(Announcement, id=announcement_id)
    announcement.delete()
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
        })

@login_required
def profile(request):
    user = request.user
    profile = user.userprofile
    if request.method == 'POST':
        if 'save_personal' in request.POST:
            personal_form = PersonalDataForm(request.POST, instance=user)
            if personal_form.is_valid():
                personal_form.save()
        elif 'save_academic' in request.POST:
            academic_form = AcademicDataForm(request.POST, instance=profile)
            if academic_form.is_valid():
                academic_form.save()
        return redirect('profile')

    personal_form = PersonalDataForm(instance=user)
    academic_form = AcademicDataForm(instance=profile)

    return render(request, 'profile.html', {
        'personal_form': personal_form,
        'academic_form': academic_form,
    })
    return render(request, 'profile.html')

@login_required
def event_participants_ajax(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    # Tylko organizator-właściciel lub admin może zobaczyć uczestników
    if event.created_by != request.user and not request.user.groups.filter(name="admin").exists():
        return JsonResponse({'error': 'Brak uprawnień'}, status=403)
    enrollments = EventEnrollment.objects.filter(event=event).select_related('user')
    html = render_to_string('events/participants_list_fragment.html', {'enrollments': enrollments, 'event': event}, request=request)
    return JsonResponse({'html': html})
