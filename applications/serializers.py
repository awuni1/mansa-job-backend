from rest_framework import serializers
from .models import Application
from jobs.serializers import JobSerializer

class ApplicationSerializer(serializers.ModelSerializer):
    job_details = JobSerializer(source='job', read_only=True)
    
    class Meta:
        model = Application
        fields = '__all__'
        read_only_fields = ('applicant', 'status', 'applied_at', 'updated_at')
