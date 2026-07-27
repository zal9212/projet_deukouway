from rest_framework import serializers

class ClientDashboardStatsSerializer(serializers.Serializer):
    total_reservations = serializers.IntegerField()
    active_reservations = serializers.IntegerField()
    completed_reservations = serializers.IntegerField()
    total_spent = serializers.DecimalField(max_digits=12, decimal_places=2)


class OwnerDashboardStatsSerializer(serializers.Serializer):
    total_properties = serializers.IntegerField()
    published_properties = serializers.IntegerField()
    pending_properties = serializers.IntegerField()
    total_reservations = serializers.IntegerField()
    occupancy_rate = serializers.FloatField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)


class SuperAdminDashboardStatsSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    total_clients = serializers.IntegerField()
    total_owners = serializers.IntegerField()
    pending_owner_approvals = serializers.IntegerField()
    total_properties = serializers.IntegerField()
    pending_property_approvals = serializers.IntegerField()
    total_volume_xof = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_commissions_xof = serializers.DecimalField(max_digits=12, decimal_places=2)
