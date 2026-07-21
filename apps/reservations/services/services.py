from django.db import transaction
from django.utils import timezone
from apps.accounts.models import User
from apps.properties.models import Property
from apps.reservations.models import ReservationRequest, Reservation, ReservationStatusHistory, ReservationHistory
from apps.reservations.choices import ReservationStatusChoices
from apps.reservations.services.exceptions import InvalidWorkflowTransition, DatesNotAvailable
import logging
import uuid

logger = logging.getLogger(__name__)

class ReservationService:

    @staticmethod
    @transaction.atomic
    def create_request(client: User, prop: Property, check_in, check_out, guests: int, special_requests: str = "") -> ReservationRequest:
        # Logique de vérification des disponibilités à intégrer ici
        # if not prop.is_available(check_in, check_out):
        #     raise DatesNotAvailable("Les dates ne sont pas disponibles.")
            
        req = ReservationRequest.objects.create(
            client=client,
            property=prop,
            check_in=check_in,
            check_out=check_out,
            guests=guests,
            status=ReservationStatusChoices.REQUESTED,
            special_requests=special_requests
        )
        
        ReservationStatusHistory.objects.create(
            request=req,
            old_status=ReservationStatusChoices.REQUESTED,
            new_status=ReservationStatusChoices.REQUESTED,
            notes="Demande créée par le client"
        )
        
        logger.info(f"Demande de réservation créée : {req.id} par {client.email}")
        return req

    @staticmethod
    @transaction.atomic
    def cancel_request(req: ReservationRequest, client: User) -> ReservationRequest:
        if req.client_id != client.id:
            raise InvalidWorkflowTransition("Non autorisé.")
            
        if req.status not in [ReservationStatusChoices.REQUESTED, ReservationStatusChoices.PENDING_OWNER_ACCEPTANCE]:
            raise InvalidWorkflowTransition("Impossible d'annuler à cette étape.")
            
        old_status = req.status
        req.status = ReservationStatusChoices.CANCELLED
        req.save(update_fields=['status'])
        
        ReservationStatusHistory.objects.create(
            request=req,
            old_status=old_status,
            new_status=ReservationStatusChoices.CANCELLED,
            notes="Annulée par le client"
        )
        
        logger.info(f"Demande de réservation annulée : {req.id} par {client.email}")
        return req

    @staticmethod
    @transaction.atomic
    def admin_validate(req: ReservationRequest, admin_user: User) -> ReservationRequest:
        if req.status != ReservationStatusChoices.REQUESTED:
            raise InvalidWorkflowTransition("La demande doit être au statut REQUESTED.")
            
        old_status = req.status
        req.status = ReservationStatusChoices.SENT_TO_OWNER
        req.save(update_fields=['status'])
        
        ReservationStatusHistory.objects.create(
            request=req,
            old_status=old_status,
            new_status=ReservationStatusChoices.SENT_TO_OWNER,
            notes=f"Validée par le SuperAdmin {admin_user.email}"
        )
        
        logger.info(f"Demande validée par l'admin : {req.id}")
        return req

    @staticmethod
    @transaction.atomic
    def admin_reject(req: ReservationRequest, admin_user: User, reason: str) -> ReservationRequest:
        if req.status != ReservationStatusChoices.REQUESTED:
            raise InvalidWorkflowTransition("La demande doit être au statut REQUESTED.")
            
        old_status = req.status
        req.status = ReservationStatusChoices.REJECTED
        req.superadmin_notes = reason
        req.save(update_fields=['status', 'superadmin_notes'])
        
        ReservationStatusHistory.objects.create(
            request=req,
            old_status=old_status,
            new_status=ReservationStatusChoices.REJECTED,
            notes=f"Rejetée par le SuperAdmin {admin_user.email} : {reason}"
        )
        
        logger.info(f"Demande rejetée par l'admin : {req.id}")
        return req

    @staticmethod
    @transaction.atomic
    def owner_accept(req: ReservationRequest, owner: User) -> ReservationRequest:
        if req.property.owner_id != owner.id:
            raise InvalidWorkflowTransition("Propriétaire non autorisé.")
            
        if req.status != ReservationStatusChoices.SENT_TO_OWNER:
            raise InvalidWorkflowTransition("La demande doit être au statut SENT_TO_OWNER.")
            
        old_status = req.status
        req.status = ReservationStatusChoices.PAYMENT_PENDING
        req.save(update_fields=['status'])
        
        ReservationStatusHistory.objects.create(
            request=req,
            old_status=old_status,
            new_status=ReservationStatusChoices.PAYMENT_PENDING,
            notes=f"Acceptée par le propriétaire {owner.email}"
        )
        
        logger.info(f"Demande acceptée par le propriétaire : {req.id}")
        return req

    @staticmethod
    @transaction.atomic
    def owner_reject(req: ReservationRequest, owner: User, reason: str) -> ReservationRequest:
        if req.property.owner_id != owner.id:
            raise InvalidWorkflowTransition("Propriétaire non autorisé.")
            
        if req.status != ReservationStatusChoices.PENDING_OWNER_ACCEPTANCE:
            raise InvalidWorkflowTransition("La demande doit être au statut PENDING_OWNER_ACCEPTANCE.")
            
        old_status = req.status
        req.status = ReservationStatusChoices.REJECTED
        req.save(update_fields=['status'])
        
        ReservationStatusHistory.objects.create(
            request=req,
            old_status=old_status,
            new_status=ReservationStatusChoices.REJECTED,
            notes=f"Rejetée par le propriétaire {owner.email} : {reason}"
        )
        
        logger.info(f"Demande rejetée par le propriétaire : {req.id}")
        return req

    @staticmethod
    @transaction.atomic
    def confirm_payment(req: ReservationRequest, total_price: float) -> Reservation:
        if req.status != ReservationStatusChoices.PAYMENT_PENDING:
            raise InvalidWorkflowTransition("La demande doit être au statut PENDING_PAYMENT.")
            
        old_status = req.status
        req.status = ReservationStatusChoices.CONFIRMED
        req.save(update_fields=['status'])
        
        ReservationStatusHistory.objects.create(
            request=req,
            old_status=old_status,
            new_status=ReservationStatusChoices.CONFIRMED,
            notes="Paiement confirmé"
        )
        
        res = Reservation.objects.create(
            request=req,
            client=req.client,
            property=req.property,
            check_in=req.check_in,
            check_out=req.check_out,
            guests=req.guests,
            total_price=total_price,
            status=ReservationStatusChoices.CONFIRMED,
            confirmation_code=str(uuid.uuid4())[:8].upper()
        )
        
        ReservationHistory.objects.create(
            reservation=res,
            action="Réservation confirmée",
            details={"payment": "success"}
        )
        
        logger.info(f"Réservation confirmée : {res.confirmation_code}")
        return res

    @staticmethod
    @transaction.atomic
    def start_stay(res: Reservation) -> Reservation:
        if res.status != ReservationStatusChoices.CONFIRMED:
            raise InvalidWorkflowTransition("Doit être confirmée pour démarrer le séjour.")
            
        res.status = ReservationStatusChoices.CHECKIN
        res.save(update_fields=['status'])
        
        ReservationHistory.objects.create(
            reservation=res,
            action="Séjour démarré"
        )
        logger.info(f"Séjour démarré : {res.confirmation_code}")
        return res

    @staticmethod
    @transaction.atomic
    def finish_stay(res: Reservation) -> Reservation:
        if res.status != ReservationStatusChoices.CHECKIN:
            raise InvalidWorkflowTransition("Doit être active pour terminer le séjour.")
            
        res.status = ReservationStatusChoices.COMPLETED
        res.save(update_fields=['status'])
        
        ReservationHistory.objects.create(
            reservation=res,
            action="Séjour terminé"
        )
        logger.info(f"Séjour terminé : {res.confirmation_code}")
        return res
