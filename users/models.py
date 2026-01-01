from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        SEEKER = "SEEKER", "Job Seeker"
        EMPLOYER = "EMPLOYER", "Employer"

    role = models.CharField(max_length=50, choices=Role.choices, default=Role.SEEKER)
    full_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    location = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    video_introduction = models.FileField(upload_to='video_profiles/', blank=True, null=True)
    
    # Social links
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    
    # Job seeker specific
    desired_salary_min = models.IntegerField(blank=True, null=True)
    desired_salary_max = models.IntegerField(blank=True, null=True)
    years_experience = models.IntegerField(default=0)
    skills = models.JSONField(default=list, blank=True)
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    job_alerts = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} ({self.role})"


class Resume(models.Model):
    """Store user resumes"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resumes')
    title = models.CharField(max_length=200, help_text='e.g. Senior Developer Resume')
    file = models.FileField(upload_to='resumes/')
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField(help_text='File size in bytes')
    
    # Parsed data (from AI)
    parsed_data = models.JSONField(blank=True, null=True)
    
    is_primary = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False, help_text='Visible to employers')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_resumes'
        ordering = ['-is_primary', '-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_primary']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.title}"
    
    def save(self, *args, **kwargs):
        # If this is set as primary, unset other primary resumes
        if self.is_primary:
            Resume.objects.filter(user=self.user, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)


class SavedSearch(models.Model):
    """Save search queries for job alerts"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_searches')
    name = models.CharField(max_length=200, help_text='e.g. Remote React Jobs')
    query = models.CharField(max_length=500)
    filters = models.JSONField(help_text='Search filters as JSON')
    
    # Alert settings
    email_alerts = models.BooleanField(default=True)
    alert_frequency = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('instant', 'Instant'),
        ],
        default='daily'
    )
    last_alerted = models.DateTimeField(blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'saved_searches'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.name}"


class Notification(models.Model):
    """User notifications"""
    
    NOTIFICATION_TYPES = [
        ('application', 'Application Update'),
        ('job_match', 'Job Match'),
        ('referral', 'Referral Update'),
        ('review', 'Review Response'),
        ('message', 'Message'),
        ('system', 'System'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=500, blank=True)
    
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.title}"
