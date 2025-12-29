from django.contrib import admin
from .models import JobView, ProfileView, SearchQuery, ApplicationEvent, DailyStats, CompanyStats


@admin.register(JobView)
class JobViewAdmin(admin.ModelAdmin):
    list_display = ['job', 'viewer', 'viewed_at', 'ip_address']
    list_filter = ['viewed_at']
    search_fields = ['job__title', 'viewer__email']
    date_hierarchy = 'viewed_at'


@admin.register(ProfileView)
class ProfileViewAdmin(admin.ModelAdmin):
    list_display = ['profile_owner', 'viewer', 'company', 'viewed_at']
    list_filter = ['viewed_at']
    search_fields = ['profile_owner__email', 'company__name']


@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ['query', 'user', 'results_count', 'searched_at']
    list_filter = ['searched_at']
    search_fields = ['query']


@admin.register(ApplicationEvent)
class ApplicationEventAdmin(admin.ModelAdmin):
    list_display = ['application', 'event_type', 'actor', 'created_at']
    list_filter = ['event_type', 'created_at']


@admin.register(DailyStats)
class DailyStatsAdmin(admin.ModelAdmin):
    list_display = ['date', 'total_jobs_posted', 'total_applications', 'total_job_views', 'new_users']
    date_hierarchy = 'date'


@admin.register(CompanyStats)
class CompanyStatsAdmin(admin.ModelAdmin):
    list_display = ['company', 'date', 'job_views', 'applications_received', 'hires']
    list_filter = ['company']
    date_hierarchy = 'date'
