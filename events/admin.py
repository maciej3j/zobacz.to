from django.contrib import admin
from .models import Event, ContactMessage, FAQ

# Register your models here.

admin.site.register(Event)
admin.site.register(ContactMessage)
admin.site.register(FAQ)