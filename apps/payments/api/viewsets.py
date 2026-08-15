from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
import uuid

from apps.payments.services.services import PaymentService
from apps.payments.services.selectors import PaymentSelector
from apps.properties.services.services import PropertyService
from apps.reservations.services.selectors import ReservationSelector
from apps.reservations.services.services import ReservationService
from apps.payments.models import Payout, Invoice
from apps.payments.api.serializers import (
    PaymentSerializer, ProcessPaymentSerializer, PayoutSerializer, InvoiceSerializer
)
from apps.payments.api.filters import PaymentFilter
from apps.core.api.permissions import IsClient, IsOwner, IsSuperAdmin

class PaymentViewSet(viewsets.ModelViewSet):
    """
    API REST de traitement des paiements entrants (Wave, Orange Money, Carte).
    """
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = PaymentFilter
    ordering_fields = ['created_at', 'amount']

    def get_permissions(self):
        if self.action in ['process', 'create']:
            return [permissions.IsAuthenticated(), IsClient()]
        elif self.action in ['commissions']:
            return [permissions.IsAuthenticated(), IsSuperAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'is_superadmin', False) or user.is_superuser:
            return PaymentSelector.get_all_payments()
        return PaymentSelector.get_payments_for_user(user.id)

    def get_serializer_class(self):
        if self.action == 'process':
            return ProcessPaymentSerializer
        return PaymentSerializer

    @action(detail=False, methods=['post'], url_path='process')
    def process(self, request):
        serializer = ProcessPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        req = ReservationSelector.get_request_by_id(str(data['request_id']))
        if not req:
            return Response({'request_id': ["Demande de réservation introuvable."]}, status=status.HTTP_404_NOT_FOUND)

        total_price = PropertyService.calculate_price_for_stay(req.property, req.check_in, req.check_out)

        res = ReservationService.confirm_payment(req, total_price=total_price)
        payment = PaymentService.create_payment(res, user=request.user, amount=total_price, method=data['method'])
        payment = PaymentService.verify_payment(payment, gateway_transaction_id=str(uuid.uuid4()))
        PaymentService.create_commission(payment)

        return Response({
            'detail': "Paiement effectué et réservation confirmée avec succès.",
            'reservation_code': res.confirmation_code,
            'payment': PaymentSerializer(payment).data
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='receipt')
    def receipt(self, request, pk=None):
        payment = self.get_object()
        receipt_data = PaymentService.generate_receipt(payment)
        return Response(receipt_data)


class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API REST d'accès et téléchargement des factures.
    """
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'is_superadmin', False) or user.is_superuser:
            return Invoice.objects.filter(is_deleted=False)
        return Invoice.objects.filter(user=user, is_deleted=False)


class PayoutViewSet(viewsets.ModelViewSet):
    """
    API REST de gestion des reversements aux propriétaires.
    """
    serializer_class = PayoutSerializer

    def get_permissions(self):
        if self.action in ['create', 'process_payout']:
            return [permissions.IsAuthenticated(), IsSuperAdmin()]
        return [permissions.IsAuthenticated(), IsOwner()]

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'is_superadmin', False) or user.is_superuser:
            return Payout.objects.filter(is_deleted=False)
        return Payout.objects.filter(owner=user, is_deleted=False)
