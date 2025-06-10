from django.db import models
from django.contrib.auth.models import User

class OrganizerRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    first_name = models.CharField("Imię", max_length=100)
    last_name = models.CharField("Nazwisko", max_length=100)
    email = models.EmailField()
    university = models.CharField("Uczelnia", max_length=200)
    field_of_study = models.CharField("Rok studiów", max_length=200)
    is_reviewed = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prośba o organizatora: {self.user.username}"

OrganizerRequest.objects.filter(is_reviewed=False).count()
