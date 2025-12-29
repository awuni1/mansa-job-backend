from django.db import models
from django.conf import settings
from jobs.models import Job

class Application(models.Model):
    class Status(models.TextChoices):
        APPLIED = 'APPLIED', 'Applied'
        REVIEWING = 'REVIEWING', 'Reviewing'
        INTERVIEW = 'INTERVIEW', 'Interview'
        REJECTED = 'REJECTED', 'Rejected'
        HIRED = 'HIRED', 'Hired'

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='applications')
    
    cover_letter = models.TextField(blank=True)
    resume_url = models.URLField(blank=True) # Link to PDF uploaded elsewhere or filed field if storing locally
    # Or models.FileField(...)
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.APPLIED)
    
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('job', 'applicant') # Prevent double application

    def __str__(self):
        return f"{self.applicant} -> {self.job}"
