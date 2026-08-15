from decimal import Decimal
from django.db.models import QuerySet, Sum
from apps.payments.models import Payment, Commission, Payout, Invoice, Refund, PlatformSettings
from apps.payments.choices import PaymentStatusChoices, PayoutStatusChoices

class PaymentSelector:

    @staticmethod
    def get_platform_settings() -> PlatformSettings:
        return PlatformSettings.load()
    
    @staticmethod
    def get_pending_payments() -> QuerySet[Payment]:
        return Payment.objects.filter(
            status=PaymentStatusChoices.PENDING, 
            is_deleted=False
        ).select_related('user', 'reservation').order_by('-created_at')

    @staticmethod
    def get_client_payments(user_id: str) -> QuerySet[Payment]:
        return Payment.objects.filter(
            user_id=user_id,
            is_deleted=False
        ).select_related('reservation', 'reservation__property').order_by('-created_at')

    @staticmethod
    def get_payments_for_user(user_id: str) -> QuerySet[Payment]:
        return PaymentSelector.get_client_payments(user_id)

    @staticmethod
    def get_owner_payouts(owner_id: str) -> QuerySet[Payout]:
        return Payout.objects.filter(
            owner_id=owner_id,
            is_deleted=False
        ).select_related('reservation', 'reservation__property').order_by('-created_at')

    @staticmethod
    def get_owner_pending_payout_total(owner_id: str) -> Decimal:
        total = Payout.objects.filter(
            owner_id=owner_id, is_deleted=False,
            status__in=[PayoutStatusChoices.PENDING, PayoutStatusChoices.PROCESSING],
        ).aggregate(total=Sum('amount'))['total']
        return total or Decimal('0')

    @staticmethod
    def get_client_invoices(user_id: str) -> QuerySet[Invoice]:
        return Invoice.objects.filter(
            user_id=user_id,
            is_deleted=False
        ).select_related('reservation', 'reservation__property').order_by('-created_at')

    @staticmethod
    def get_all_payments(search_query: str = None, status: str = None) -> QuerySet[Payment]:
        from django.db.models import Q
        qs = Payment.objects.filter(
            is_deleted=False
        ).select_related('user', 'reservation', 'reservation__property')
        if search_query:
            qs = qs.filter(
                Q(gateway_transaction_id__icontains=search_query) |
                Q(user__email__icontains=search_query) |
                Q(reservation__confirmation_code__icontains=search_query)
            )
        if status:
            qs = qs.filter(status=status)
        return qs.order_by('-created_at')

    @staticmethod
    def get_all_payouts(search_query: str = None, status: str = None) -> QuerySet[Payout]:
        from django.db.models import Q
        qs = Payout.objects.filter(
            is_deleted=False
        ).select_related('owner', 'reservation', 'reservation__property')
        if search_query:
            qs = qs.filter(
                Q(owner__email__icontains=search_query) |
                Q(reservation__confirmation_code__icontains=search_query)
            )
        if status:
            qs = qs.filter(status=status)
        return qs.order_by('-created_at')

    @staticmethod
    def get_payment_by_id(payment_id: str) -> Payment | None:
        return Payment.objects.filter(id=payment_id, is_deleted=False).select_related(
            'user', 'reservation', 'reservation__property', 'commission'
        ).first()

    @staticmethod
    def get_payout_by_id(payout_id: str) -> Payout | None:
        return Payout.objects.filter(id=payout_id, is_deleted=False).select_related(
            'owner', 'reservation', 'reservation__property'
        ).first()

    @staticmethod
    def get_all_commissions() -> QuerySet[Commission]:
        return Commission.objects.filter(
            is_deleted=False
        ).select_related('payment', 'payment__reservation').order_by('-created_at')

    @staticmethod
    def get_all_refunds() -> QuerySet[Refund]:
        return Refund.objects.filter(
            is_deleted=False
        ).select_related('payment', 'payment__user').order_by('-created_at')

    @staticmethod
    def get_commissions_for_month(year: int, month: int) -> QuerySet[Commission]:
        return Commission.objects.filter(
            created_at__year=year,
            created_at__month=month,
            is_deleted=False
        ).select_related('payment')
