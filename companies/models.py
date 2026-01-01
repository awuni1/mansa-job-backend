from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Company(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='companies')
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    website = models.URLField(blank=True)
    location = models.CharField(max_length=255)
    description = models.TextField()
    # Verified status
    is_verified = models.BooleanField(default=False)
    verification_requested = models.BooleanField(default=False)
    verification_documents = models.JSONField(blank=True, null=True, help_text='URLs to verification documents')
    verified_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'companies'
        verbose_name_plural = 'Companies'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_verified']),
        ]

    def __str__(self):
        return self.name


class CompanyReview(models.Model):
    """Employee reviews of companies"""
    
    EMPLOYMENT_STATUS_CHOICES = [
        ('current', 'Current Employee'),
        ('former', 'Former Employee'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='company_reviews')
    employment_status = models.CharField(max_length=20, choices=EMPLOYMENT_STATUS_CHOICES)
    job_title = models.CharField(max_length=200)
    
    # Ratings (1-5 stars)
    overall_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    work_life_balance = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    salary_benefits = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    job_security = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    management = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    culture = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    
    # Review content
    title = models.CharField(max_length=200)
    pros = models.TextField()
    cons = models.TextField()
    advice_to_management = models.TextField(blank=True)
    
    # Verification
    is_verified = models.BooleanField(default=False)
    is_anonymous = models.BooleanField(default=False)
    
    # Engagement
    helpful_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'company_reviews'
        ordering = ['-created_at']
        unique_together = ['company', 'reviewer']  # One review per user per company
        indexes = [
            models.Index(fields=['company', '-overall_rating']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.reviewer.email} review of {self.company.name}"


class CompanyReferral(models.Model):
    """Employee referral system"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('contacted', 'Contacted'),
        ('interviewing', 'Interviewing'),
        ('hired', 'Hired'),
        ('rejected', 'Rejected'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='referrals')
    referrer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='referrals_made')
    candidate_email = models.EmailField()
    candidate_name = models.CharField(max_length=200)
    candidate_phone = models.CharField(max_length=50, blank=True)
    candidate_resume = models.FileField(upload_to='referral_resumes/', blank=True, null=True)
    job_title = models.CharField(max_length=200)
    message = models.TextField(help_text='Why this candidate is a good fit')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    status_updated_at = models.DateTimeField(auto_now=True)
    
    # Rewards
    reward_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reward_paid = models.BooleanField(default=False)
    reward_paid_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'company_referrals'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['referrer', '-created_at']),
            models.Index(fields=['company', 'status']),
            models.Index(fields=['candidate_email']),
        ]

    def __str__(self):
        return f"{self.referrer.email} referred {self.candidate_name} to {self.company.name}"


class ReviewHelpful(models.Model):
    """Track who found reviews helpful"""
    review = models.ForeignKey(CompanyReview, on_delete=models.CASCADE, related_name='helpful_votes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'review_helpful'
        unique_together = ['review', 'user']
        indexes = [
            models.Index(fields=['review']),
        ]

