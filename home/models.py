from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Document(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    filename = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/')
    pages = models.PositiveIntegerField(default=0)  # optional, can store page count
    size_bytes = models.PositiveBigIntegerField(default=0)
    upload_ts = models.DateTimeField(auto_now_add=True)
    status_choices = [
        ('pending', 'Pending'),
        ('processed', 'Processed'),
        ('error', 'Error'),
    ]
    status = models.CharField(max_length=20, choices=status_choices, default='pending')

    def __str__(self):
        return self.filename