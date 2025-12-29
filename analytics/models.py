from django.db import models
from django.conf import settings
from jobs.models import Job
from companies.models import Company


class JobView(models.Model):
    """Track job listing views"""
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='views')
    viewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='job_views'
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['job', 'viewed_at']),
            models.Index(fields=['viewer', 'viewed_at']),
        ]

    def __str__(self):
        return f"View of {self.job} at {self.viewed_at}"


class ProfileView(models.Model):
    """Track profile/resume views by employers"""
    profile_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile_views_received'
    )
    viewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='profile_views_made'
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='profile_views'
    )
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['profile_owner', 'viewed_at']),
        ]

    def __str__(self):
        return f"View of {self.profile_owner}'s profile at {self.viewed_at}"


class SearchQuery(models.Model):
    """Track search queries for analytics"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='search_queries'
    )
    query = models.CharField(max_length=500)
    filters = models.JSONField(default=dict, blank=True)
    results_count = models.PositiveIntegerField(default=0)
    searched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-searched_at']
        verbose_name_plural = 'Search queries'

    def __str__(self):
        return f"Search: {self.query[:50]}..."


class ApplicationEvent(models.Model):
    """Track application lifecycle events"""
    class EventType(models.TextChoices):
        VIEWED = 'VIEWED', 'Application Viewed'
        STATUS_CHANGED = 'STATUS_CHANGED', 'Status Changed'
        NOTE_ADDED = 'NOTE_ADDED', 'Note Added'
        INTERVIEW_SCHEDULED = 'INTERVIEW_SCHEDULED', 'Interview Scheduled'
        OFFER_MADE = 'OFFER_MADE', 'Offer Made'
        REJECTED = 'REJECTED', 'Rejected'
        WITHDRAWN = 'WITHDRAWN', 'Withdrawn'

    application = models.ForeignKey(
        'applications.Application',
        on_delete=models.CASCADE,
        related_name='events'
    )
    event_type = models.CharField(max_length=30, choices=EventType.choices)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='application_events'
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['application', 'created_at']),
        ]

    def __str__(self):
        return f"{self.event_type} on {self.application}"


class DailyStats(models.Model):
    """Aggregated daily statistics"""
    date = models.DateField(unique=True)
    
    # Global stats
    total_jobs_posted = models.PositiveIntegerField(default=0)
    total_applications = models.PositiveIntegerField(default=0)
    total_job_views = models.PositiveIntegerField(default=0)
    total_searches = models.PositiveIntegerField(default=0)
    new_users = models.PositiveIntegerField(default=0)
    active_users = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-date']
        verbose_name_plural = 'Daily stats'

    def __str__(self):
        return f"Stats for {self.date}"


class CompanyStats(models.Model):
    """Company-specific analytics"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='stats')
    date = models.DateField()
    
    job_views = models.PositiveIntegerField(default=0)
    applications_received = models.PositiveIntegerField(default=0)
    profile_views = models.PositiveIntegerField(default=0)
    hires = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-date']
        unique_together = ['company', 'date']
        verbose_name_plural = 'Company stats'

    def __str__(self):
        return f"{self.company} stats for {self.date}"
