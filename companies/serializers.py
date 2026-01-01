from rest_framework import serializers
from .models import Company, CompanyReview, CompanyReferral, ReviewHelpful
from django.db.models import Avg, Count


class CompanySerializer(serializers.ModelSerializer):
    average_rating = serializers.SerializerMethodField()
    total_reviews = serializers.SerializerMethodField()
    
    class Meta:
        model = Company
        fields = '__all__'
        read_only_fields = ('owner', 'is_verified', 'verified_at', 'created_at', 'updated_at')
    
    def get_average_rating(self, obj):
        avg = obj.reviews.aggregate(Avg('overall_rating'))['overall_rating__avg']
        return round(avg, 1) if avg else None
    
    def get_total_reviews(self, obj):
        return obj.reviews.count()


class CompanyReviewSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.SerializerMethodField()
    is_helpful = serializers.SerializerMethodField()
    
    class Meta:
        model = CompanyReview
        fields = [
            'id', 'company', 'reviewer', 'reviewer_name', 'employment_status', 
            'job_title', 'overall_rating', 'work_life_balance', 'salary_benefits',
            'job_security', 'management', 'culture', 'title', 'pros', 'cons',
            'advice_to_management', 'is_verified', 'is_anonymous', 'helpful_count',
            'is_helpful', 'created_at', 'updated_at'
        ]
        read_only_fields = ('reviewer', 'is_verified', 'helpful_count', 'created_at', 'updated_at')
    
    def get_reviewer_name(self, obj):
        if obj.is_anonymous:
            return 'Anonymous'
        return obj.reviewer.full_name or obj.reviewer.email.split('@')[0]
    
    def get_is_helpful(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ReviewHelpful.objects.filter(review=obj, user=request.user).exists()
        return False


class CompanyReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyReview
        fields = [
            'company', 'employment_status', 'job_title', 'overall_rating',
            'work_life_balance', 'salary_benefits', 'job_security', 'management',
            'culture', 'title', 'pros', 'cons', 'advice_to_management', 'is_anonymous'
        ]
    
    def validate(self, data):
        # Check if user already reviewed this company
        user = self.context['request'].user
        company = data['company']
        
        if CompanyReview.objects.filter(company=company, reviewer=user).exists():
            raise serializers.ValidationError('You have already reviewed this company')
        
        return data
    
    def create(self, validated_data):
        validated_data['reviewer'] = self.context['request'].user
        return super().create(validated_data)


class CompanyReferralSerializer(serializers.ModelSerializer):
    referrer_name = serializers.CharField(source='referrer.full_name', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = CompanyReferral
        fields = [
            'id', 'company', 'company_name', 'referrer', 'referrer_name',
            'candidate_email', 'candidate_name', 'candidate_phone', 
            'candidate_resume', 'job_title', 'message', 'status',
            'status_updated_at', 'reward_amount', 'reward_paid',
            'reward_paid_at', 'created_at'
        ]
        read_only_fields = ('referrer', 'status', 'status_updated_at', 'reward_amount', 'reward_paid', 'reward_paid_at', 'created_at')
    
    def create(self, validated_data):
        validated_data['referrer'] = self.context['request'].user
        return super().create(validated_data)


class CompanyReferralStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=CompanyReferral.STATUS_CHOICES)
    reward_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
