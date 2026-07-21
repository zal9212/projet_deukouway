from django.db.models import QuerySet
from apps.reservations.models import ReservationRequest, Reservation
from apps.reservations.choices import ReservationStatusChoices

class ReservationSelector:
    
    @staticmethod
    def get_pending_requests() -> QuerySet[ReservationRequest]:
        return ReservationRequest.objects.filter(
            status=ReservationStatusChoices.REQUESTED, 
            is_deleted=False
        ).select_related('client', 'property')
        
    @staticmethod
    def get_user_reservations(user_id: str) -> QuerySet[Reservation]:
        return Reservation.objects.filter(
            client_id=user_id, 
            is_deleted=False
        ).select_related('property', 'request').order_by('-created_at')
