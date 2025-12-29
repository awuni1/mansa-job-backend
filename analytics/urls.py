from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    JobViewViewSet, EmployerAnalyticsView, SeekerAnalyticsView,
    TrackJobViewAPIView, TrackSearchAPIView
)

router = DefaultRouter()
router.register(r'job-views', JobViewViewSet, basename='job-views')

urlpatterns = [
    path('', include(router.urls)),
    path('employer/', EmployerAnalyticsView.as_view(), name='employer-analytics'),
    path('seeker/', SeekerAnalyticsView.as_view(), name='seeker-analytics'),
    path('track/job/<int:job_id>/', TrackJobViewAPIView.as_view(), name='track-job-view'),
    path('track/search/', TrackSearchAPIView.as_view(), name='track-search'),
]
