from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Count, Q
from django_ratelimit.decorators import ratelimit

from .models import Company, CompanyReview, CompanyReferral, ReviewHelpful
from .serializers import (
    CompanySerializer, CompanyReviewSerializer, CompanyReviewCreateSerializer,
    CompanyReferralSerializer, CompanyReferralStatusUpdateSerializer
)


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
    
    @action(detail=True, methods=['get'])
    def reviews(self, request, slug=None):
        """Get all reviews for a company"""
        company = self.get_object()
        reviews = company.reviews.all()
        
        # Filter by rating if provided
        rating_filter = request.query_params.get('rating')
        if rating_filter:
            reviews = reviews.filter(overall_rating=rating_filter)
        
        # Sort options
        sort_by = request.query_params.get('sort', '-created_at')
        if sort_by == 'helpful':
            reviews = reviews.order_by('-helpful_count', '-created_at')
        else:
            reviews = reviews.order_by(sort_by)
        
        serializer = CompanyReviewSerializer(reviews, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def referrals(self, request, slug=None):
        """Get referrals for a company (owner only)"""
        company = self.get_object()
        
        if company.owner != request.user:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        
        referrals = company.referrals.all()
        serializer = CompanyReferralSerializer(referrals, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def request_verification(self, request, slug=None):
        """Request company verification"""
        company = self.get_object()
        
        if company.owner != request.user:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        
        if company.is_verified:
            return Response({'error': 'Company already verified'}, status=status.HTTP_400_BAD_REQUEST)
        
        company.verification_requested = True
        company.verification_documents = request.data.get('documents', [])
        company.save()
        
        return Response({'message': 'Verification request submitted'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@ratelimit(key='user', rate='5/h', method='POST')
def create_review(request):
    """Create a company review"""
    serializer = CompanyReviewCreateSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        review = serializer.save()
        return Response(
            CompanyReviewSerializer(review, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_review_helpful(request, review_id):
    """Mark a review as helpful"""
    review = get_object_or_404(CompanyReview, id=review_id)
    
    # Check if already marked helpful
    helpful, created = ReviewHelpful.objects.get_or_create(
        review=review,
        user=request.user
    )
    
    if created:
        review.helpful_count += 1
        review.save()
        return Response({'message': 'Marked as helpful'})
    else:
        # Remove helpful mark
        helpful.delete()
        review.helpful_count = max(0, review.helpful_count - 1)
        review.save()
        return Response({'message': 'Removed helpful mark'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_reviews(request):
    """Get current user's reviews"""
    reviews = CompanyReview.objects.filter(reviewer=request.user)
    serializer = CompanyReviewSerializer(reviews, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@ratelimit(key='user', rate='10/h', method='POST')
def create_referral(request):
    """Submit an employee referral"""
    serializer = CompanyReferralSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        referral = serializer.save()
        return Response(
            CompanyReferralSerializer(referral).data,
            status=status.HTTP_201_CREATED
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_referrals(request):
    """Get current user's referrals"""
    referrals = CompanyReferral.objects.filter(referrer=request.user)
    serializer = CompanyReferralSerializer(referrals, many=True)
    return Response(serializer.data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_referral_status(request, referral_id):
    """Update referral status (company owner only)"""
    referral = get_object_or_404(CompanyReferral, id=referral_id)
    
    # Check if user is company owner
    if referral.company.owner != request.user:
        return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
    
    serializer = CompanyReferralStatusUpdateSerializer(data=request.data)
    if serializer.is_valid():
        referral.status = serializer.validated_data['status']
        
        # Set reward if hired
        if serializer.validated_data['status'] == 'hired' and 'reward_amount' in serializer.validated_data:
            referral.reward_amount = serializer.validated_data['reward_amount']
        
        referral.save()
        
        return Response(CompanyReferralSerializer(referral).data)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def company_stats(request, slug):
    """Get company statistics"""
    company = get_object_or_404(Company, slug=slug)
    
    reviews = company.reviews.all()
    review_stats = reviews.aggregate(
        average_rating=Avg('overall_rating'),
        total_reviews=Count('id'),
        average_work_life=Avg('work_life_balance'),
        average_salary=Avg('salary_benefits'),
        average_security=Avg('job_security'),
        average_management=Avg('management'),
        average_culture=Avg('culture')
    )
    
    # Rating distribution
    rating_distribution = {}
    for i in range(1, 6):
        rating_distribution[i] = reviews.filter(overall_rating=i).count()
    
    return Response({
        'company': CompanySerializer(company).data,
        'stats': review_stats,
        'rating_distribution': rating_distribution
    })
