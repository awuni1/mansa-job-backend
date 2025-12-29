from rest_framework import viewsets, permissions, filters
from .models import Job
from .serializers import JobSerializer

class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.filter(is_active=True).order_by('-created_at')
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'description', 'company__name', 'skills']

    def perform_create(self, serializer):
        # Assign company based on user's company? 
        # For now, require company_id in body
        serializer.save()
