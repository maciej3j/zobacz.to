from django.contrib import admin
from .models import Event, ContactMessage, FAQ, Announcement

# Register your models here.

admin.site.register(Event)
admin.site.register(ContactMessage)
admin.site.register(FAQ)
admin.site.register(Announcement)