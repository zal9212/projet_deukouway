from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from decimal import Decimal
from django.db.models import Sum

from apps.core.api.cache import cache_response
from apps.core.api.permissions import IsSuperAdmin, IsOwner, IsClient
from apps.reservations.models import Reservation, ReservationRequest
from apps.properties.models import Property
from apps.payments.models import Payment, Commission
from apps.accounts.models import User
from apps.dashboard.api.serializers import (
    ClientDashboardStatsSerializer, OwnerDashboardStatsSerializer, SuperAdminDashboardStatsSerializer
)

class DashboardViewSet(viewsets.ViewSet):
    """
    API REST centralisant la mise à disposition des KPIs et métriques du Dashboard.
    """
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='client-stats', permission_classes=[permissions.IsAuthenticated, IsClient])
    @cache_response(timeout=60, key_prefix='dashboard:client')
    def client_stats(self, request):
        user = request.user
        requests_qs = ReservationRequest.objects.filter(client=user, is_deleted=False)
        reservations_qs = Reservation.objects.filter(client=user, is_deleted=False)

        total_spent = Payment.objects.filter(user=user, status='SUCCESS').aggregate(s=Sum('amount'))['s'] or Decimal('0.00')

        data = {
            'total_reservations': requests_qs.count(),
            'active_reservations': reservations_qs.filter(status__in=['CONFIRMED', 'CHECKIN']).count(),
            'completed_reservations': reservations_qs.filter(status='COMPLETED').count(),
            'total_spent': total_spent
        }
        return Response(ClientDashboardStatsSerializer(data).data)

    @action(detail=False, methods=['get'], url_path='owner-stats', permission_classes=[permissions.IsAuthenticated, IsOwner])
    @cache_response(timeout=60, key_prefix='dashboard:owner')
    def owner_stats(self, request):
        user = request.user
        properties_qs = Property.objects.filter(owner=user, is_deleted=False)
        reservations_qs = Reservation.objects.filter(property__owner=user, is_deleted=False)

        revenue = Payment.objects.filter(reservation__property__owner=user, status='SUCCESS').aggregate(s=Sum('amount'))['s'] or Decimal('0.00')

        total_props = properties_qs.count()
        published_props = properties_qs.filter(status='PUBLISHED').count()
        pending_props = properties_qs.filter(status='PENDING').count()

        occupancy_rate = (published_props / total_props * 100) if total_props > 0 else 0.0

        data = {
            'total_properties': total_props,
            'published_properties': published_props,
            'pending_properties': pending_props,
            'total_reservations': reservations_qs.count(),
            'occupancy_rate': round(occupancy_rate, 2),
            'total_revenue': revenue
        }
        return Response(OwnerDashboardStatsSerializer(data).data)

    @action(detail=False, methods=['get'], url_path='admin-stats', permission_classes=[permissions.IsAuthenticated, IsSuperAdmin])
    @cache_response(timeout=60, key_prefix='dashboard:admin')
    def admin_stats(self, request):
        total_users = User.objects.filter(is_deleted=False).count()
        clients = User.objects.filter(is_client=True, is_deleted=False).count()
        owners = User.objects.filter(is_owner=True, is_deleted=False).count()
        pending_owners = User.objects.filter(is_owner=True, is_verified=False, is_deleted=False).count()

        total_props = Property.objects.filter(is_deleted=False).count()
        pending_props = Property.objects.filter(status='PENDING', is_deleted=False).count()

        total_volume = Payment.objects.filter(status='SUCCESS').aggregate(s=Sum('amount'))['s'] or Decimal('0.00')
        total_commissions = Commission.objects.aggregate(s=Sum('amount'))['s'] or Decimal('0.00')

        data = {
            'total_users': total_users,
            'total_clients': clients,
            'total_owners': owners,
            'pending_owner_approvals': pending_owners,
            'total_properties': total_props,
            'pending_property_approvals': pending_props,
            'total_volume_xof': total_volume,
            'total_commissions_xof': total_commissions
        }
        return Response(SuperAdminDashboardStatsSerializer(data).data)
