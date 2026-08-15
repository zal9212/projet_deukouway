from django.db.models import QuerySet, Q
from apps.reservations.models import ReservationRequest, Reservation
from apps.reservations.choices import ReservationStatusChoices

# Statuts d'une demande qui "bloquent" encore les dates (le workflow n'est pas
# terminé ni annulé/refusé) : une nouvelle demande sur les mêmes dates doit être
# refusée tant que l'une de ces demandes existe.
ACTIVE_REQUEST_STATUSES = [
    ReservationStatusChoices.REQUESTED,
    ReservationStatusChoices.UNDER_REVIEW,
    ReservationStatusChoices.SENT_TO_OWNER,
    ReservationStatusChoices.OWNER_ACCEPTED,
    ReservationStatusChoices.PAYMENT_PENDING,
    ReservationStatusChoices.PAID,
    ReservationStatusChoices.CONFIRMED,
]

# Statuts d'une réservation ferme qui occupent réellement le logement.
ACTIVE_RESERVATION_STATUSES = [
    ReservationStatusChoices.CONFIRMED,
    ReservationStatusChoices.CHECKIN,
    ReservationStatusChoices.CHECKOUT,
]

class ReservationSelector:

    @staticmethod
    def has_overlapping_active_booking(property_id, check_in, check_out) -> bool:
        """
        Indique si le logement a déjà une demande active ou une réservation ferme
        qui chevauche l'intervalle [check_in, check_out[ demandé.
        """
        overlapping_requests = ReservationRequest.objects.filter(
            property_id=property_id,
            status__in=ACTIVE_REQUEST_STATUSES,
            is_deleted=False,
            check_in__lt=check_out,
            check_out__gt=check_in,
        ).exists()
        if overlapping_requests:
            return True

        overlapping_reservations = Reservation.objects.filter(
            property_id=property_id,
            status__in=ACTIVE_RESERVATION_STATUSES,
            is_deleted=False,
            check_in__lt=check_out,
            check_out__gt=check_in,
        ).exists()
        return overlapping_reservations

    @staticmethod
    def get_pending_requests() -> QuerySet[ReservationRequest]:
        return ReservationRequest.objects.filter(
            status=ReservationStatusChoices.REQUESTED, 
            is_deleted=False
        ).select_related('client', 'property').order_by('-created_at')

    @staticmethod
    def get_all_requests() -> QuerySet[ReservationRequest]:
        return ReservationRequest.objects.filter(
            is_deleted=False
        ).select_related('client', 'property').order_by('-created_at')

    @staticmethod
    def get_client_reservations(user_id: str, search_query: str = None, status: str = None) -> QuerySet[Reservation]:
        qs = Reservation.objects.filter(
            client_id=user_id,
            is_deleted=False
        ).select_related('property', 'request').prefetch_related('property__images').order_by('-created_at')
        if search_query:
            qs = qs.filter(
                Q(property__title__icontains=search_query) |
                Q(confirmation_code__icontains=search_query)
            )
        if status == 'confirmed':
            qs = qs.filter(status__in=[
                ReservationStatusChoices.CONFIRMED, ReservationStatusChoices.CHECKIN, ReservationStatusChoices.CHECKOUT,
            ])
        elif status == 'completed':
            qs = qs.filter(status=ReservationStatusChoices.COMPLETED)
        return qs

    @staticmethod
    def get_reservations_for_client(user_id: str) -> QuerySet[Reservation]:
        return ReservationSelector.get_client_reservations(user_id)

    @staticmethod
    def get_reservations_for_owner(owner_id: str) -> QuerySet[Reservation]:
        return Reservation.objects.filter(
            property__owner_id=owner_id,
            is_deleted=False
        ).select_related('property', 'request').order_by('-created_at')

    @staticmethod
    def get_client_requests(user_id: str) -> QuerySet[ReservationRequest]:
        return ReservationRequest.objects.filter(
            client_id=user_id,
            is_deleted=False
        ).select_related('property').prefetch_related('property__images').order_by('-created_at')

    @staticmethod
    def get_requests_for_client(user_id: str) -> QuerySet[ReservationRequest]:
        return ReservationSelector.get_client_requests(user_id)

    @staticmethod
    def get_owner_requests(owner_id: str) -> QuerySet[ReservationRequest]:
        return ReservationRequest.objects.filter(
            property__owner_id=owner_id,
            is_deleted=False
        ).select_related('client', 'property').order_by('-created_at')

    @staticmethod
    def get_requests_for_owner(owner_id: str) -> QuerySet[ReservationRequest]:
        return ReservationSelector.get_owner_requests(owner_id)

    @staticmethod
    def get_reservation_by_id(reservation_id: str) -> Reservation | None:
        return Reservation.objects.filter(
            id=reservation_id,
            is_deleted=False
        ).select_related('client', 'property', 'request').first()

    @staticmethod
    def get_request_by_id(request_id: str) -> ReservationRequest | None:
        return ReservationRequest.objects.filter(
            id=request_id,
            is_deleted=False
        ).select_related('client', 'property').first()

    @staticmethod
    def get_all_reservations(search_query: str = None, status: str = None) -> QuerySet[Reservation]:
        from django.db.models import Q
        qs = Reservation.objects.filter(
            is_deleted=False
        ).select_related('client', 'property', 'property__owner')
        if search_query:
            qs = qs.filter(
                Q(code__icontains=search_query) |
                Q(client__email__icontains=search_query) |
                Q(property__title__icontains=search_query)
            )
        if status:
            qs = qs.filter(status=status)
        return qs.order_by('-created_at')
