from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Event(models.Model):
    title = models.CharField("Tytuł", max_length=200)
    description = models.TextField("Opis wydarzenia")
    date = models.DateTimeField("Data")
    location = models.CharField("Lokalizacja", max_length=200)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_events")

    def __str__(self):
        return self.title
    
    def participants(self):
        return User.objects.filter(eventenrollment__event=self)
    
class EventEnrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'event')  

class EventComment(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField("Komentarz")
    rating = models.PositiveSmallIntegerField("Ocena", choices=[(i, i) for i in range(1, 6)])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.rating}/5): {self.comment[:30]}"
    
class Rating(models.Model):
    event = models.ForeignKey('Event', related_name='ratings', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stars = models.PositiveSmallIntegerField()  # 1–5
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('event', 'user')  # jeden użytkownik może ocenić dane wydarzenie tylko raz

    def __str__(self):
        return f'{self.user} rated {self.event} - {self.stars}★'