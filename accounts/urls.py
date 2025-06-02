from django.urls import path
from django.contrib.auth.views import LoginView
from .views import (
    SignUpView,
    organizer_requests_list,
    approve_organizer_request,
    reject_organizer_request,
    organizer_request_create,
)

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path("login/", LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("organizer-requests/", organizer_requests_list, name="organizer_requests_list"),
    path("organizer-requests/approve/<int:pk>/", approve_organizer_request, name="approve_organizer_request"),
    path("organizer-requests/reject/<int:pk>/", reject_organizer_request, name="reject_organizer_request"),
    path('organizer-request/', organizer_request_create, name='organizer_request_create'),
]