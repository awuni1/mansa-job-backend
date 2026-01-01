from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes, action
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .serializers import (
    RegisterSerializer, UserSerializer, UserProfileUpdateSerializer,
    ResumeSerializer, SavedSearchSerializer, NotificationSerializer
)
from .models import Resume, SavedSearch, Notification

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer


class ProfileView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    def patch(self, request):
        serializer = UserProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(UserSerializer(request.user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResumeViewSet(viewsets.ModelViewSet):
    serializer_class = ResumeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Resume.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def set_primary(self, request, pk=None):
        """Set this resume as primary"""
        resume = self.get_object()
        
        # Unset other primary resumes
        Resume.objects.filter(user=request.user, is_primary=True).update(is_primary=False)
        
        resume.is_primary = True
        resume.save()
        
        return Response(ResumeSerializer(resume).data)
    
    @action(detail=True, methods=['post'])
    def parse(self, request, pk=None):
        """Parse resume with AI"""
        from ai_services.gemini_service import parse_resume
        
        resume = self.get_object()
        
        try:
            # Read resume file
            resume.file.seek(0)
            text = resume.file.read().decode('utf-8', errors='ignore')
            
            # Parse with AI
            parsed_data = parse_resume(text)
            
            # Save parsed data
            resume.parsed_data = parsed_data
            resume.save()
            
            return Response({
                'message': 'Resume parsed successfully',
                'data': parsed_data
            })
        except Exception as e:
            return Response({
                'error': 'Failed to parse resume',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SavedSearchViewSet(viewsets.ModelViewSet):
    serializer_class = SavedSearchSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return SavedSearch.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def toggle_alerts(self, request, pk=None):
        """Toggle email alerts for this search"""
        saved_search = self.get_object()
        saved_search.email_alerts = not saved_search.email_alerts
        saved_search.save()
        
        return Response(SavedSearchSerializer(saved_search).data)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        
        return Response(NotificationSerializer(notification).data)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
        
        return Response({'message': 'All notifications marked as read'})
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        
        return Response({'count': count})
