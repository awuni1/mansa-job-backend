"""
AI Services Models
Store AI-related data and usage logs
"""

from django.db import models
from users.models import User
from jobs.models import Job


class ParsedResume(models.Model):
    """Store parsed resume data from AI"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='parsed_resumes')
    raw_text = models.TextField(help_text='Original resume text')
    parsed_data = models.JSONField(help_text='Structured data extracted by AI')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ai_parsed_resumes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"Resume for {self.user.email} - {self.created_at.strftime('%Y-%m-%d')}"


class JobMatch(models.Model):
    """Store job match calculations"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_matches')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='candidate_matches')
    match_score = models.IntegerField(help_text='Match score 0-100')
    match_data = models.JSONField(help_text='Detailed match analysis')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_job_matches'
        ordering = ['-match_score', '-created_at']
        unique_together = ['user', 'job']
        indexes = [
            models.Index(fields=['user', '-match_score']),
            models.Index(fields=['job', '-match_score']),
        ]
    
    def __str__(self):
        return f"{self.user.email} <-> {self.job.title} ({self.match_score}%)"


class InterviewPrep(models.Model):
    """Store generated interview questions"""
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='interview_questions')
    questions = models.JSONField(help_text='List of generated interview questions')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_interview_prep'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['job', '-created_at']),
        ]
    
    def __str__(self):
        return f"Interview questions for {self.job.title}"


class AIUsageLog(models.Model):
    """Track AI API usage for monitoring and billing"""
    
    SERVICE_TYPES = [
        ('resume_parse', 'Resume Parsing'),
        ('job_match', 'Job Matching'),
        ('job_description', 'Job Description Generation'),
        ('search_parse', 'Search Query Parsing'),
        ('interview_questions', 'Interview Questions'),
        ('salary_insights', 'Salary Insights'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ai_usage')
    service_type = models.CharField(max_length=50, choices=SERVICE_TYPES)
    input_tokens = models.IntegerField(default=0, help_text='Approximate input tokens')
    output_tokens = models.IntegerField(default=0, help_text='Approximate output tokens')
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_usage_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['service_type', '-created_at']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        user_str = self.user.email if self.user else 'Anonymous'
        return f"{user_str} - {self.get_service_type_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

