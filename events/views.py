from django.shortcuts import render, redirect
from django.views.generic import ListView
from .models import Event
from .forms import EventForm
from django.utils.timezone import now
from .decorators import organizer_required

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
