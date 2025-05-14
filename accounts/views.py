from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import Group
from .forms import CustomUserCreationForm
from .decorators import admin_required
from .models import OrganizerRequest


class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Konto zostało utworzone. Możesz się teraz zalogować.")
        return response

@admin_required
def organizer_requests_list(request):
    requests = OrganizerRequest.objects.filter(is_reviewed=False)
    return render(request, "registration/organizer_requests_list.html", {"requests": requests})

@admin_required
def approve_organizer_request(request, pk):
    req = get_object_or_404(OrganizerRequest, pk=pk)
    req.is_reviewed = True
    req.is_approved = True
    req.save()
    organizer_group, _ = Group.objects.get_or_create(name="organizer")
    req.user.groups.add(organizer_group)
    return redirect("organizer_requests_list")

@admin_required
def reject_organizer_request(request, pk):
    req = get_object_or_404(OrganizerRequest, pk=pk)
    req.is_reviewed = True
    req.is_approved = False
    req.save()
    return redirect("organizer_requests_list")