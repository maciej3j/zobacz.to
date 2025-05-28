from django.shortcuts import render, redirect
from django.views.generic import ListView
from .models import Event
from .forms import EventForm
from .models import EventEnrollment
from django.utils.timezone import now
from .decorators import organizer_required
from .decorators import student_required
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required

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

@organizer_required
def add_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('events_list')
    else:
        form = EventForm()
    return render(request, 'events/add_event.html', {'form': form})


def home(request):
    events = Event.objects.all()
    return render(request, 'home.html', {'events': events})

@student_required
def enroll_in_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if event.eventenrollment_set.filter(user=request.user).exists():
        messages.info(request, "Jesteś już zapisany na to wydarzenie.")
    else:
        event.eventenrollment_set.create(user=request.user)
        messages.success(request, "Pomyślnie zapisano na wydarzenie!")

    return redirect('events_list')

@login_required
def home(request):
    # Pobierz wydarzenia, na które zalogowany użytkownik się zapisał
    enrolled_events = Event.objects.filter(eventenrollment__user=request.user).order_by('date')
    
    return render(request, 'home.html', {'enrolled_events': enrolled_events})
