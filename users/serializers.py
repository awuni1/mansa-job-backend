from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Resume, SavedSearch, Notification

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'role', 'first_name', 'last_name',
            'full_name', 'phone', 'location', 'bio', 'profile_picture', 'video_introduction',
            'linkedin_url', 'github_url', 'portfolio_url',
            'desired_salary_min', 'desired_salary_max', 'years_experience',
            'skills', 'email_notifications', 'job_alerts', 'created_at'
        )
        read_only_fields = ('id', 'created_at')


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'full_name', 'phone', 'location', 'bio', 'profile_picture', 'video_introduction',
            'linkedin_url', 'github_url', 'portfolio_url',
            'desired_salary_min', 'desired_salary_max', 'years_experience',
            'skills', 'email_notifications', 'job_alerts'
        )


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'role', 'first_name', 'last_name', 'full_name')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role=validated_data.get('role', 'SEEKER'),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            full_name=validated_data.get('full_name', ''),
        )
        return user


class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = [
            'id', 'title', 'file', 'file_name', 'file_size',
            'parsed_data', 'is_primary', 'is_public', 'created_at', 'updated_at'
        ]
        read_only_fields = ('id', 'file_name', 'file_size', 'created_at', 'updated_at')
    
    def create(self, validated_data):
        file = validated_data.get('file')
        if file:
            validated_data['file_name'] = file.name
            validated_data['file_size'] = file.size
        
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class SavedSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedSearch
        fields = [
            'id', 'name', 'query', 'filters', 'email_alerts',
            'alert_frequency', 'last_alerted', 'is_active', 'created_at'
        ]
        read_only_fields = ('id', 'last_alerted', 'created_at')
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'title', 'message', 'link',
            'is_read', 'read_at', 'created_at'
        ]
        read_only_fields = ('id', 'created_at')


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        token['email'] = user.email
        return token
