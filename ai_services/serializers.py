"""
AI Services Serializers
"""

from rest_framework import serializers
from .models import ParsedResume, JobMatch, InterviewPrep


class ParsedResumeSerializer(serializers.ModelSerializer):
    """Serializer for parsed resume data"""
    
    class Meta:
        model = ParsedResume
        fields = ['id', 'parsed_data', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class JobMatchSerializer(serializers.ModelSerializer):
    """Serializer for job match data"""
    job_title = serializers.CharField(source='job.title', read_only=True)
    company_name = serializers.CharField(source='job.company.name', read_only=True)
    
    class Meta:
        model = JobMatch
        fields = ['id', 'job', 'job_title', 'company_name', 'match_score', 'match_data', 'created_at']
        read_only_fields = ['id', 'created_at']


class InterviewPrepSerializer(serializers.ModelSerializer):
    """Serializer for interview questions"""
    job_title = serializers.CharField(source='job.title', read_only=True)
    
    class Meta:
        model = InterviewPrep
        fields = ['id', 'job', 'job_title', 'questions', 'created_at']
        read_only_fields = ['id', 'created_at']


# Input serializers for API requests
class ResumeParseRequestSerializer(serializers.Serializer):
    """Serializer for resume parsing request"""
    resume_text = serializers.CharField(min_length=50, max_length=50000)


class JobMatchRequestSerializer(serializers.Serializer):
    """Serializer for job match request"""
    job_id = serializers.IntegerField()
    candidate_profile = serializers.JSONField()


class JobDescriptionRequestSerializer(serializers.Serializer):
    """Serializer for job description generation request"""
    title = serializers.CharField(max_length=200)
    company = serializers.CharField(max_length=200, required=False, allow_blank=True)
    location = serializers.CharField(max_length=200, required=False, allow_blank=True)
    type = serializers.CharField(max_length=50, required=False, allow_blank=True)
    requirements = serializers.ListField(
        child=serializers.CharField(max_length=500),
        required=False,
        allow_empty=True
    )


class SearchParseRequestSerializer(serializers.Serializer):
    """Serializer for search query parsing request"""
    query = serializers.CharField(min_length=2, max_length=500)


class InterviewQuestionsRequestSerializer(serializers.Serializer):
    """Serializer for interview questions generation request"""
    role = serializers.CharField(max_length=200)
    skills = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        allow_empty=True
    )
    experience_level = serializers.CharField(max_length=50, required=False, allow_blank=True)


class SalaryInsightsRequestSerializer(serializers.Serializer):
    """Serializer for salary insights request"""
    role = serializers.CharField(max_length=200)
    location = serializers.CharField(max_length=200, required=False, allow_blank=True)
    experience_level = serializers.CharField(max_length=50, required=False, allow_blank=True)
