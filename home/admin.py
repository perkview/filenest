from django.contrib import admin
from .models import ContactMessage, UserExtra, ProcessedDocument, Document, Message

# Register your models here.
admin.site.register(ContactMessage)
admin.site.register(UserExtra)
admin.site.register(ProcessedDocument)
admin.site.register(Document)
admin.site.register(Message)