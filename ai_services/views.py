"""
AI Services Views
REST API endpoints for AI-powered features
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_ratelimit.decorators import ratelimit
from django.views.decorators.cache import cache_page

from .gemini_service import (
    parse_resume,
    calculate_job_match,
    generate_job_description,
    parse_search_query,
    generate_interview_questions,
    get_salary_insights,
)
from .models import ParsedResume, JobMatch, InterviewPrep, AIUsageLog
from .serializers import (
    ParsedResumeSerializer,
    JobMatchSerializer,
    InterviewPrepSerializer,
    ResumeParseRequestSerializer,
    JobMatchRequestSerializer,
    JobDescriptionRequestSerializer,
    SearchParseRequestSerializer,
    InterviewQuestionsRequestSerializer,
    SalaryInsightsRequestSerializer,
)
from jobs.models import Job


def log_ai_usage(user, service_type, success=True, error_message=None):
    """Helper function to log AI API usage"""
    AIUsageLog.objects.create(
        user=user,
        service_type=service_type,
        success=success,
        error_message=error_message
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@ratelimit(key='user', rate='10/m', method='POST')
def parse_resume_view(request):
    """
    Parse resume text and extract structured data
    
    POST /api/ai/parse-resume/
    Body: { "resume_text": "..." }
    
    Returns: Structured resume data
    """
    serializer = ResumeParseRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    resume_text = serializer.validated_data['resume_text']
    
    try:
        parsed_data = parse_resume(resume_text)
        
        # Save to database
        parsed_resume = ParsedResume.objects.create(
            user=request.user,
            raw_text=resume_text,
            parsed_data=parsed_data
        )
        
        log_ai_usage(request.user, 'resume_parse', success=True)
        
        return Response({
            'id': parsed_resume.id,
            'data': parsed_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        log_ai_usage(request.user, 'resume_parse', success=False, error_message=str(e))
        return Response({
            'error': 'Failed to parse resume',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@ratelimit(key='user', rate='10/m', method='POST')
def calculate_job_match_view(request):
    """
    Calculate match score between candidate and job
    
    POST /api/ai/job-match/
    Body: {
        "job_id": 123,
        "candidate_profile": {
            "skills": [...],
            "yearsExperience": 5,
            "location": "...",
            "desiredSalary": "..."
        }
    }
    
    Returns: Match analysis with score
    """
    serializer = JobMatchRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    job_id = serializer.validated_data['job_id']
    candidate_profile = serializer.validated_data['candidate_profile']
    
    try:
        job = Job.objects.get(id=job_id)
        
        # Prepare job requirements
        job_requirements = {
            'title': job.title,
            'skills': job.required_skills or [],
            'experienceLevel': job.experience_level,
            'location': job.location,
            'salaryRange': f"${job.salary_min}-${job.salary_max}" if job.salary_min else "Negotiable"
        }
        
        match_data = calculate_job_match(candidate_profile, job_requirements)
        
        # Save or update match
        job_match, created = JobMatch.objects.update_or_create(
            user=request.user,
            job=job,
            defaults={
                'match_score': match_data.get('matchScore', 50),
                'match_data': match_data
            }
        )
        
        log_ai_usage(request.user, 'job_match', success=True)
        
        return Response(match_data, status=status.HTTP_200_OK)
        
    except Job.DoesNotExist:
        return Response({
            'error': 'Job not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        log_ai_usage(request.user, 'job_match', success=False, error_message=str(e))
        return Response({
            'error': 'Failed to calculate job match',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@ratelimit(key='user', rate='10/m', method='POST')
def generate_job_description_view(request):
    """
    Generate job description from basic info
    
    POST /api/ai/generate-job-description/
    Body: {
        "title": "...",
        "company": "...",
        "location": "...",
        "type": "...",
        "requirements": [...]
    }
    
    Returns: Generated job description
    """
    serializer = JobDescriptionRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    job_info = serializer.validated_data
    
    try:
        job_desc = generate_job_description(job_info)
        
        log_ai_usage(request.user, 'job_description', success=True)
        
        return Response(job_desc, status=status.HTTP_200_OK)
        
    except Exception as e:
        log_ai_usage(request.user, 'job_description', success=False, error_message=str(e))
        return Response({
            'error': 'Failed to generate job description',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@ratelimit(key='user', rate='10/m', method='POST')
def parse_search_query_view(request):
    """
    Parse natural language search query
    
    POST /api/ai/parse-search/
    Body: { "query": "..." }
    
    Returns: Structured search filters
    """
    serializer = SearchParseRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    query = serializer.validated_data['query']
    
    try:
        filters = parse_search_query(query)
        
        log_ai_usage(request.user, 'search_parse', success=True)
        
        return Response(filters, status=status.HTTP_200_OK)
        
    except Exception as e:
        log_ai_usage(request.user, 'search_parse', success=False, error_message=str(e))
        return Response({
            'error': 'Failed to parse search query',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@ratelimit(key='user', rate='10/m', method='POST')
def generate_interview_questions_view(request):
    """
    Generate interview questions for a role
    
    POST /api/ai/interview-questions/
    Body: {
        "role": "...",
        "skills": [...],
        "experience_level": "..."
    }
    
    Returns: List of interview questions
    """
    serializer = InterviewQuestionsRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    role = serializer.validated_data['role']
    skills = serializer.validated_data.get('skills', [])
    experience_level = serializer.validated_data.get('experience_level', 'mid')
    
    try:
        questions = generate_interview_questions(role, skills, experience_level)
        
        log_ai_usage(request.user, 'interview_questions', success=True)
        
        return Response({
            'questions': questions
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        log_ai_usage(request.user, 'interview_questions', success=False, error_message=str(e))
        return Response({
            'error': 'Failed to generate interview questions',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@ratelimit(key='user', rate='10/m', method='POST')
def get_salary_insights_view(request):
    """
    Get salary insights for a role
    
    POST /api/ai/salary-insights/
    Body: {
        "role": "...",
        "location": "...",
        "experience_level": "..."
    }
    
    Returns: Salary insights with ranges and trends
    """
    serializer = SalaryInsightsRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    role = serializer.validated_data['role']
    location = serializer.validated_data.get('location', 'Africa')
    experience_level = serializer.validated_data.get('experience_level', 'mid')
    
    try:
        insights = get_salary_insights(role, location, experience_level)
        
        log_ai_usage(request.user, 'salary_insights', success=True)
        
        return Response(insights, status=status.HTTP_200_OK)
        
    except Exception as e:
        log_ai_usage(request.user, 'salary_insights', success=False, error_message=str(e))
        return Response({
            'error': 'Failed to get salary insights',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_parsed_resumes(request):
    """Get user's parsed resumes"""
    resumes = ParsedResume.objects.filter(user=request.user)
    serializer = ParsedResumeSerializer(resumes, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_job_matches(request):
    """Get user's job matches"""
    matches = JobMatch.objects.filter(user=request.user)
    serializer = JobMatchSerializer(matches, many=True)
    return Response(serializer.data)

