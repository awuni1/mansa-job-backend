from rest_framework import serializers
from .models import JobView, ProfileView, SearchQuery, ApplicationEvent, DailyStats, CompanyStats


class JobViewSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source='job.title', read_only=True)
    
    class Meta:
        model = JobView
        fields = ['id', 'job', 'job_title', 'viewed_at']
        read_only_fields = ['viewer', 'ip_address', 'user_agent', 'referrer', 'viewed_at']


class ProfileViewSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = ProfileView
        fields = ['id', 'company', 'company_name', 'viewed_at']
        read_only_fields = ['profile_owner', 'viewer', 'viewed_at']


class SearchQuerySerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchQuery
        fields = ['id', 'query', 'filters', 'results_count', 'searched_at']
        read_only_fields = ['user', 'searched_at']


class ApplicationEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationEvent
        fields = ['id', 'application', 'event_type', 'metadata', 'created_at']
        read_only_fields = ['actor', 'created_at']


class DailyStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyStats
        fields = '__all__'


class CompanyStatsSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = CompanyStats
        fields = '__all__'


class AnalyticsSummarySerializer(serializers.Serializer):
    """Serializer for analytics summary responses"""
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    total_views = serializers.IntegerField()
    total_applications = serializers.IntegerField()
    conversion_rate = serializers.FloatField()
