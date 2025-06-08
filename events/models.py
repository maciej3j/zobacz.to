from django.db import models
from django.contrib.auth.models import User
from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    university = models.CharField("Uczelnia", max_length=100, blank=True)
    faculty = models.CharField("Wydział", max_length=100, blank=True)
    field_of_study = models.CharField("Kierunek studiów", max_length=100, blank=True)
    STUDY_YEARS = [(i, str(i)) for i in range(1, 8)] # można wybrać jedynie rok studiów od 1 do 7
    study_year = models.PositiveIntegerField("Rok studiów", choices=STUDY_YEARS, null=True, blank=True)
    main_discipline = models.CharField("Dyscyplina naukowa", max_length=100, blank=True)
    interests = models.TextField("Zainteresowania", blank=True)

    def __str__(self):
        return f"Profil użytkownika: {self.user.username}"

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
    
class Announcement(models.Model):
    CATEGORY_CHOICES = [
        ('ogloszenie', 'Ogłoszenie'),
        ('nowosc', 'Nowość'),
        ('wydarzenie', 'Wydarzenie'),
        ('informacja', 'Informacja'),
        ('edukacja', 'Edukacja'),
    ]
    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class ContactMessage(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_answered = models.BooleanField(default=False)
    answer = models.TextField(blank=True, null=True)

class FAQ(models.Model):
    question = models.CharField(max_length=300, verbose_name="Pytanie")
    answer = models.TextField(verbose_name="Odpowiedź")

    def __str__(self):
        return self.question