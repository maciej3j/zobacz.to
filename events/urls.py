from django.urls import path
from . import views
from .views import EventListView

urlpatterns = [
    path("", EventListView.as_view(), name="events_list" ),
    path('add/', views.add_event, name='add_event'),
    path('zapisz-sie/<int:event_id>/', views.enroll_in_event, name='enroll_in_event'),
    path('delete/<int:event_id>/', views.delete_event, name='delete_event'),
    path('event/<int:event_id>/', views.event_detail, name='event_detail'),
    path('events/<int:event_id>/unenroll/', views.unenroll_from_event, name='unenroll_event'),
    path('kontakt/', views.contact, name='contact'),
    path('profile/', views.profile, name='profile'),
    path('event/<int:event_id>/participants-ajax/', views.event_participants_ajax, name='event_participants_ajax'),
    path('mark_admin_answer_seen/', views.mark_admin_answer_seen, name='mark_admin_answer_seen'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('event/<int:event_id>/edit/', views.edit_event, name='edit_event'),
    path("calendar/", views.custom_calendar_view, name="custom-calendar"),
    path("calendar/<int:year>/<int:month>/", views.custom_calendar_view, name="custom-calendar"),
]
