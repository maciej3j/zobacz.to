from django.db import models

# Create your models here.
class Event(models.Model):
    title = models.CharField("Tytuł", max_length=200)
    description = models.TextField("Opis wydarzenia")
    date = models.DateTimeField("Data")
    location = models.CharField("Lokalizacja", max_length=200)

    def __str__(self):
        return self.title