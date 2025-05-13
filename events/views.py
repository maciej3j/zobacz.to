from django.shortcuts import render, redirect
from django.views.generic import ListView
from .models import Event
from .forms import EventForm

# Create your views here.

class EventListView(ListView):
    model = Event
    template_name = "events_list.html"
    context_object_name = "events"

def add_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('events_list')  # Zmień na odpowiednią nazwę widoku
    else:
        form = EventForm()
    return render(request, 'add_event.html', {'form': form})


def home(request):
    events = Event.objects.all()
    return render(request, 'home.html', {'events': events})
