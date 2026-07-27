from rest_framework import serializers
from apps.reservations.models import ReservationRequest, Reservation, ReservationHistory, ReservationStatusHistory
from apps.properties.api.serializers import PropertyListSerializer

class ReservationRequestSerializer(serializers.ModelSerializer):
    property_detail = PropertyListSerializer(source='property', read_only=True)
    client_email = serializers.EmailField(source='client.email', read_only=True)

    class Meta:
        model = ReservationRequest
        fields = [
            'id', 'client_email', 'property', 'property_detail',
            'check_in', 'check_out', 'guests', 'status',
            'special_requests', 'created_at'
        ]
        read_only_fields = ['id', 'client_email', 'status', 'created_at']


class ReservationRequestCreateSerializer(serializers.Serializer):
    property_id = serializers.UUIDField(required=True)
    check_in = serializers.DateField(required=True)
    check_out = serializers.DateField(required=True)
    guests = serializers.IntegerField(min_value=1, required=True)
    special_requests = serializers.CharField(required=False, allow_blank=True)


class ReservationSerializer(serializers.ModelSerializer):
    property_detail = PropertyListSerializer(source='property', read_only=True)

    class Meta:
        model = Reservation
        fields = [
            'id', 'confirmation_code', 'property_detail', 'check_in', 'check_out',
            'guests', 'total_price', 'status', 'created_at'
        ]
        read_only_fields = ['id', 'confirmation_code', 'status', 'created_at']


class ReservationStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ReservationStatusHistory
        fields = ['id', 'old_status', 'new_status', 'notes', 'created_at']
