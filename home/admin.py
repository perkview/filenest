from django.contrib import admin
from .models import ContactMessage, UserExtra, ProcessedDocument

# Register your models here.
admin.site.register(ContactMessage)
admin.site.register(UserExtra)
admin.site.register(ProcessedDocument)