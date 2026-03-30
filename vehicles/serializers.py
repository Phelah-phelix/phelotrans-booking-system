from rest_framework import serializers
from .models import Vehicle

class VehicleSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    
    class Meta:
        model = Vehicle
        fields = '__all__'
        read_only_fields = ['owner', 'created_at', 'updated_at']
