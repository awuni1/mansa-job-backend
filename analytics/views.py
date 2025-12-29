from django.shortcuts import render
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import JobView, ProfileView, SearchQuery, ApplicationEvent, DailyStats, CompanyStats
from .serializers import (
    JobViewSerializer, ProfileViewSerializer, SearchQuerySerializer,
    DailyStatsSerializer, CompanyStatsSerializer, AnalyticsSummarySerializer
)


class AnalyticsMixin:
    """Mixin for common analytics utilities"""
    
    def get_date_range(self, request):
        """Get date range from request params"""
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        return start_date, end_date


class JobViewViewSet(viewsets.ModelViewSet):
    """Track and retrieve job views"""
    serializer_class = JobViewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.role == 'EMPLOYER':
            # Employers see views for their jobs
            return JobView.objects.filter(job__company__owner=user)
        return JobView.objects.none()

    def perform_create(self, serializer):
        """Record a job view"""
        request = self.request
        serializer.save(
            viewer=request.user if request.user.is_authenticated else None,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            referrer=request.META.get('HTTP_REFERER', '')
        )

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


class EmployerAnalyticsView(APIView, AnalyticsMixin):
    """Analytics dashboard for employers"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role != 'EMPLOYER':
            return Response(
                {'error': 'Only employers can access analytics'},
                status=status.HTTP_403_FORBIDDEN
            )

        start_date, end_date = self.get_date_range(request)

        # Get user's companies
        companies = user.companies.all()
        
        # Aggregate stats
        job_views = JobView.objects.filter(
            job__company__in=companies,
            viewed_at__date__gte=start_date,
            viewed_at__date__lte=end_date
        )

        total_views = job_views.count()
        views_by_day = job_views.annotate(
            date=TruncDate('viewed_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')

        # Applications stats
        from applications.models import Application
        applications = Application.objects.filter(
            job__company__in=companies,
            applied_at__date__gte=start_date,
            applied_at__date__lte=end_date
        )

        total_applications = applications.count()
        applications_by_status = applications.values('status').annotate(
            count=Count('id')
        )

        # Top performing jobs
        top_jobs = job_views.values(
            'job__id', 'job__title'
        ).annotate(
            views=Count('id')
        ).order_by('-views')[:5]

        return Response({
            'period': {
                'start': start_date,
                'end': end_date
            },
            'summary': {
                'total_views': total_views,
                'total_applications': total_applications,
                'conversion_rate': round(
                    (total_applications / total_views * 100) if total_views > 0 else 0, 2
                )
            },
            'views_by_day': list(views_by_day),
            'applications_by_status': list(applications_by_status),
            'top_jobs': list(top_jobs)
        })


class SeekerAnalyticsView(APIView, AnalyticsMixin):
    """Analytics for job seekers"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        start_date, end_date = self.get_date_range(request)

        # Profile views received
        profile_views = ProfileView.objects.filter(
            profile_owner=user,
            viewed_at__date__gte=start_date,
            viewed_at__date__lte=end_date
        )

        total_profile_views = profile_views.count()
        views_by_day = profile_views.annotate(
            date=TruncDate('viewed_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')

        # Application stats
        from applications.models import Application
        applications = Application.objects.filter(
            applicant=user,
            applied_at__date__gte=start_date,
            applied_at__date__lte=end_date
        )

        total_applications = applications.count()
        applications_by_status = applications.values('status').annotate(
            count=Count('id')
        )

        # Recent companies that viewed profile
        recent_viewers = profile_views.select_related('company').values(
            'company__name', 'company__id'
        ).distinct()[:10]

        return Response({
            'period': {
                'start': start_date,
                'end': end_date
            },
            'summary': {
                'profile_views': total_profile_views,
                'applications_sent': total_applications,
            },
            'profile_views_by_day': list(views_by_day),
            'applications_by_status': list(applications_by_status),
            'recent_profile_viewers': list(recent_viewers)
        })


class TrackJobViewAPIView(APIView):
    """Simple endpoint to track job views"""
    permission_classes = [permissions.AllowAny]

    def post(self, request, job_id):
        from jobs.models import Job
        
        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            return Response(
                {'error': 'Job not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Create view record
        JobView.objects.create(
            job=job,
            viewer=request.user if request.user.is_authenticated else None,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            referrer=request.META.get('HTTP_REFERER', '')
        )

        return Response({'status': 'tracked'}, status=status.HTTP_201_CREATED)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


class TrackSearchAPIView(APIView):
    """Track search queries"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        query = request.data.get('query', '')
        filters = request.data.get('filters', {})
        results_count = request.data.get('results_count', 0)

        if query:
            SearchQuery.objects.create(
                user=request.user if request.user.is_authenticated else None,
                query=query,
                filters=filters,
                results_count=results_count
            )

        return Response({'status': 'tracked'}, status=status.HTTP_201_CREATED)
