from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from drf_spectacular.utils import extend_schema

from apps.reservations.services.services import ReservationService
from apps.reservations.services.selectors import ReservationSelector
from apps.properties.services.selectors import PropertySelector
from apps.reservations.models import ReservationRequest, Reservation
from apps.reservations.api.serializers import (
    ReservationRequestSerializer, ReservationRequestCreateSerializer,
    ReservationSerializer, ReservationStatusHistorySerializer
)
from apps.reservations.api.filters import ReservationRequestFilter
from apps.core.api.permissions import IsClient, IsOwner, IsSuperAdmin, IsReservationOwner

class ReservationRequestViewSet(viewsets.ModelViewSet):
    """
    API REST de gestion du workflow des demandes de réservation.
    """
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = ReservationRequestFilter
    ordering_fields = ['created_at', 'check_in']

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated(), IsClient()]
        elif self.action in ['cancel']:
            return [permissions.IsAuthenticated(), IsClient()]
        elif self.action in ['owner_accept', 'owner_reject']:
            return [permissions.IsAuthenticated(), IsOwner()]
        elif self.action in ['admin_validate', 'admin_reject']:
            return [permissions.IsAuthenticated(), IsSuperAdmin()]
        return [permissions.IsAuthenticated(), IsReservationOwner()]

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'is_superadmin', False) or user.is_superuser:
            return ReservationSelector.get_all_requests()
        elif getattr(user, 'is_owner', False):
            return ReservationSelector.get_requests_for_owner(user.id)
        return ReservationSelector.get_requests_for_client(user.id)

    def get_serializer_class(self):
        if self.action == 'create':
            return ReservationRequestCreateSerializer
        return ReservationRequestSerializer

    def create(self, request, *args, **kwargs):
        serializer = ReservationRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        prop = PropertySelector.get_property_by_id(str(data['property_id']))
        if not prop:
            return Response({'property_id': ["Propriété introuvable."]}, status=status.HTTP_404_NOT_FOUND)

        req = ReservationService.create_request(
            client=request.user,
            prop=prop,
            check_in=data['check_in'],
            check_out=data['check_out'],
            guests=data['guests'],
            special_requests=data.get('special_requests', '')
        )
        return Response(ReservationRequestSerializer(req).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        req = self.get_object()
        req = ReservationService.cancel_request(req, client=request.user)
        return Response({'detail': "Demande de réservation annulée.", 'request': ReservationRequestSerializer(req).data})

    @action(detail=True, methods=['post'], url_path='admin-validate')
    def admin_validate(self, request, pk=None):
        req = self.get_object()
        req = ReservationService.admin_validate(req, admin_user=request.user)
        return Response({'detail': "Demande validée par l'administrateur et transmise au propriétaire.", 'request': ReservationRequestSerializer(req).data})

    @action(detail=True, methods=['post'], url_path='owner-accept')
    def owner_accept(self, request, pk=None):
        req = self.get_object()
        req = ReservationService.owner_accept(req, owner=request.user)
        return Response({'detail': "Demande acceptée par le propriétaire. En attente de paiement.", 'request': ReservationRequestSerializer(req).data})

    @action(detail=True, methods=['post'], url_path='owner-reject')
    def owner_reject(self, request, pk=None):
        req = self.get_object()
        reason = request.data.get('reason', 'Refusé par le propriétaire')
        req = ReservationService.owner_reject(req, owner=request.user, reason=reason)
        return Response({'detail': "Demande refusée par le propriétaire.", 'request': ReservationRequestSerializer(req).data})

    @action(detail=True, methods=['get'], url_path='timeline')
    def timeline(self, request, pk=None):
        req = self.get_object()
        history = req.status_history.all().order_by('-created_at')
        serializer = ReservationStatusHistorySerializer(history, many=True)
        return Response(serializer.data)


class ReservationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API REST de consultation des réservations fermes et confirmées.
    """
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'is_superadmin', False) or user.is_superuser:
            return ReservationSelector.get_all_reservations()
        elif getattr(user, 'is_owner', False):
            return ReservationSelector.get_reservations_for_owner(user.id)
        return ReservationSelector.get_reservations_for_client(user.id)
