from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CompanyViewSet, create_review, mark_review_helpful, my_reviews,
    create_referral, my_referrals, update_referral_status, company_stats
)

router = DefaultRouter()
router.register(r'', CompanyViewSet, basename='company')

urlpatterns = [
    # Company reviews
    path('reviews/create/', create_review, name='create-review'),
    path('reviews/<int:review_id>/helpful/', mark_review_helpful, name='mark-review-helpful'),
    path('reviews/my/', my_reviews, name='my-reviews'),
    
    # Referrals
    path('referrals/create/', create_referral, name='create-referral'),
    path('referrals/my/', my_referrals, name='my-referrals'),
    path('referrals/<int:referral_id>/status/', update_referral_status, name='update-referral-status'),
    
    # Stats
    path('<slug:slug>/stats/', company_stats, name='company-stats'),
    
    # Company CRUD (must be last)
    path('', include(router.urls)),
]
