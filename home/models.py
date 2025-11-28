from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class ContactMessage(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    # Helpful for admin or dashboard
    is_resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - {self.subject}"
    

from django.utils import timezone
from django.db.models import Count, Q

class UserExtra(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # User Profile
    full_name = models.CharField(max_length=150, blank=True)

    # Subscription / Plan
    plan = models.CharField(
        max_length=50,
        choices=[
            ('free', 'Free'),
            ('pro', 'Pro'),
            ('student', 'Student'),
            ('team', 'Team')
        ],
        default='free'
    )
    subscription_active = models.BooleanField(default=False)
    subscription_start = models.DateTimeField(blank=True, null=True)
    subscription_end = models.DateTimeField(blank=True, null=True)

    # User Activity / Stats
    total_pdfs_processed = models.PositiveIntegerField(default=0)
    total_words_processed = models.PositiveIntegerField(default=0)
    total_pages_processed = models.PositiveIntegerField(default=0)
    total_points_earned = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} Profile"

    class Meta:
        verbose_name = "User Extra"
        verbose_name_plural = "User Extras"

    # -------------------------------
    # Helper: can process document today
    # -------------------------------
    def can_process_today(self):
        """
        Checks if user can process a document today.
        Free users: max 2 per day.
        Other plans: unlimited.
        """
        if self.plan != 'free':
            return True  # Pro, Student, Team have no daily limit

        # Free user: count processed today
        from .models import ProcessedDocument
        today = timezone.now().date()
        processed_today = ProcessedDocument.objects.filter(
            user=self.user,
            created_at__date=today,
            deleted_by_user=False
        ).count()

        return processed_today < 2



class ProcessedDocument(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pdf_file = models.FileField(upload_to='uploaded_pdfs/')
    generated_pdf = models.FileField(upload_to='generated_pdfs/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    processed_count = models.PositiveIntegerField(default=0)
    num_pages = models.PositiveIntegerField(default=0)
    num_words = models.PositiveIntegerField(default=0)

    deleted_by_user = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.pdf_file.name} ({self.user.username})"
