from django.db import models
from django.conf import settings
from companies.models import Company

class Job(models.Model):
    class JobType(models.TextChoices):
        FULL_TIME = 'FULL_TIME', 'Full Time'
        PART_TIME = 'PART_TIME', 'Part Time'
        CONTRACT = 'CONTRACT', 'Contract'
        FREELANCE = 'FREELANCE', 'Freelance'
        INTERNSHIP = 'INTERNSHIP', 'Internship'

    title = models.CharField(max_length=255)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='jobs')
    location = models.CharField(max_length=255) # e.g. "Accra, Ghana" or "Remote"
    is_remote = models.BooleanField(default=False)
    
    job_type = models.CharField(max_length=50, choices=JobType.choices, default=JobType.FULL_TIME)
    salary_range = models.CharField(max_length=100, blank=True) # e.g. "$50k - $80k"
    
    description = models.TextField()
    requirements = models.TextField()
    
    skills = models.JSONField(default=list) # Simple list of strings for now, or M2M if we want a Skills model
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} at {self.company.name}"
