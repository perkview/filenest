from django.db import models
from django.contrib.auth.models import User
import os

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



def user_document_path(instance, filename):
    """
    Upload documents to a user-specific folder
    Example: documents/user_5/filename.pdf
    """
    return f'documents/user_{instance.user.id}/{filename}'

class Document(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    
    # Original file uploaded
    file = models.FileField(upload_to=user_document_path)
    
    # File metadata
    name = models.CharField(max_length=255, blank=True)  # original file name
    file_size = models.PositiveIntegerField(blank=True, null=True)  # size in bytes
    file_type = models.CharField(max_length=50, blank=True)  # extension, e.g., pdf, docx
    
    # Optional: store document title or description
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True, help_text="Optional description of the document")
    
    # Status / Processing fields
    is_processed = models.BooleanField(default=False, help_text="Has this document been processed by AI?")
    processed_at = models.DateTimeField(blank=True, null=True)
    
    # Soft-delete flag
    is_deleted = models.BooleanField(default=False, help_text="True if deleted by the user")

    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.name or self.file.name

    def save(self, *args, **kwargs):
        """
        Override save to auto-populate file metadata
        """
        if self.file:
            self.name = os.path.basename(self.file.name)
            self.file_size = self.file.size
            self.file_type = os.path.splitext(self.file.name)[1][1:].lower()  # e.g., pdf, docx
        super().save(*args, **kwargs)

class Message(models.Model):
    """
    Represents a single message in a document-based chat session.
    """

    # Link to the document (chat session)
    document = models.ForeignKey(
        'Document', 
        on_delete=models.CASCADE, 
        related_name='messages',
        help_text="The document/chat session to which this message belongs"
    )

    # The user who sent the message
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        null=True,  # Null for AI messages
        blank=True,
        help_text="User who sent the message; null if sent by AI"
    )

    # Content of the message
    content = models.TextField(help_text="Text content of the message")

    # Who sent it? True = user, False = AI
    is_user = models.BooleanField(default=True, help_text="True if user sent, False if AI")

    # Optional metadata
    message_type = models.CharField(
        max_length=50, 
        choices=[
            ('text', 'Text'),
            ('summary', 'Summary'),
            ('question', 'Question'),
            ('key_points', 'Key Points')
        ],
        default='text',
        help_text="Type of message: text, summary, question, key points, etc."
    )

    # Order in chat (auto increment per document)
    order = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Sequential order of the message in this document's chat"
    )

    # Status flags
    is_processed = models.BooleanField(default=True, help_text="If the AI response is fully processed")
    is_deleted = models.BooleanField(default=False, help_text="Soft delete message, hidden from user")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, help_text="When the message was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="Last updated timestamp")

    class Meta:
        ordering = ['order', 'created_at']  # Ensure messages display in correct chat order

    def save(self, *args, **kwargs):
        if self.order is None:
            last_msg = Message.objects.filter(document=self.document).order_by('-order').first()
            self.order = (last_msg.order or 0) + 1 if last_msg else 1
        super().save(*args, **kwargs)


    def __str__(self):
        sender = 'User' if self.is_user else 'AI'
        return f"{sender} ({self.order}): {self.content[:50]}"
