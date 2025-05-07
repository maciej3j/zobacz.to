from django.urls import path
from . import views
from .views import EventListView

urlpatterns = [
    path("", EventListView.as_view(), name="events_list" ),
    path('add/', views.add_event, name='add_event')
]