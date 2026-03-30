from rest_framework import serializers
from .models import Booking
from vehicles.serializers import VehicleSerializer

class BookingSerializer(serializers.ModelSerializer):
    vehicle_details = VehicleSerializer(source='vehicle', read_only=True)
    customer_name = serializers.CharField(source='customer.username', read_only=True)
    
    class Meta:
        model = Booking
        fields = '__all__'
        read_only_fields = ['customer', 'total_price', 'created_at', 'updated_at']
