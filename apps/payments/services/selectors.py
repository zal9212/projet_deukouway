from django.db.models import QuerySet
from apps.payments.models import Payment, Commission, Payout
from apps.payments.choices import PaymentStatusChoices

class PaymentSelector:
    
    @staticmethod
    def get_pending_payments() -> QuerySet[Payment]:
        return Payment.objects.filter(
            status=PaymentStatusChoices.PENDING, 
            is_deleted=False
        )
        
    @staticmethod
    def get_commissions_for_month(year: int, month: int) -> QuerySet[Commission]:
        return Commission.objects.filter(
            created_at__year=year,
            created_at__month=month,
            is_deleted=False
        )
