"""
AI Services URL Configuration
"""

from django.urls import path
from . import views

app_name = 'ai_services'

urlpatterns = [
    # AI Generation endpoints
    path('parse-resume/', views.parse_resume_view, name='parse-resume'),
    path('job-match/', views.calculate_job_match_view, name='job-match'),
    path('generate-job-description/', views.generate_job_description_view, name='generate-job-description'),
    path('parse-search/', views.parse_search_query_view, name='parse-search'),
    path('interview-questions/', views.generate_interview_questions_view, name='interview-questions'),
    path('salary-insights/', views.get_salary_insights_view, name='salary-insights'),
    
    # User data endpoints
    path('my-resumes/', views.get_user_parsed_resumes, name='my-resumes'),
    path('my-job-matches/', views.get_user_job_matches, name='my-job-matches'),
]
