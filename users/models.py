from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        SEEKER = "SEEKER", "Job Seeker"
        EMPLOYER = "EMPLOYER", "Employer"

    role = models.CharField(max_length=50, choices=Role.choices, default=Role.SEEKER)
    
    # Profile fields can be in separate models (SeekerProfile, EmployerProfile)
    # or added here if simple. We'll start with separate models for scalability.

    def __str__(self):
        return f"{self.username} ({self.role})"
