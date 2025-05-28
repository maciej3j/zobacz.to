from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Event(models.Model):
    title = models.CharField("Tytuł", max_length=200)
    description = models.TextField("Opis wydarzenia")
    date = models.DateTimeField("Data")
    location = models.CharField("Lokalizacja", max_length=200)

    def __str__(self):
        return self.title
    
class EventEnrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'event')  