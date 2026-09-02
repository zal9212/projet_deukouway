from decimal import Decimal
from django.db import transaction
from django.urls import reverse
from apps.accounts.models import User
from apps.properties.models import Property
from apps.reservations.models import ReservationRequest, Reservation, ReservationStatusHistory, ReservationHistory
from apps.reservations.choices import ReservationStatusChoices
from apps.reservations.services.exceptions import InvalidWorkflowTransition, DatesNotAvailable
from apps.reservations.services.selectors import ReservationSelector
from apps.notifications.services.services import NotificationService
import logging
import uuid

logger = logging.getLogger(__name__)

class ReservationService:

    @staticmethod
    @transaction.atomic
    def create_request(client: User, prop: Property, check_in, check_out, guests: int, special_requests: str = "") -> ReservationRequest:
        if check_out <= check_in:
            raise DatesNotAvailable("La date de départ doit être postérieure à la date d'arrivée.")

        if ReservationSelector.has_overlapping_active_booking(prop.id, check_in, check_out):
            raise DatesNotAvailable("Ce logement n'est plus disponible pour les dates sélectionnées.")

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
            
        if req.status not in [ReservationStatusChoices.REQUESTED, ReservationStatusChoices.SENT_TO_OWNER, ReservationStatusChoices.PAYMENT_PENDING, ReservationStatusChoices.PAYMENT_LINK_SENT]:
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
    def admin_send_payment_link(req: ReservationRequest, admin_user: User) -> ReservationRequest:
        """
        Le SuperAdmin valide la disponibilité et transmet le lien de paiement au client.
        REQUESTED -> PAYMENT_LINK_SENT
        """
        if req.status != ReservationStatusChoices.REQUESTED:
            raise InvalidWorkflowTransition("La demande doit être au statut REQUESTED.")

        old_status = req.status
        req.status = ReservationStatusChoices.PAYMENT_LINK_SENT
        req.save(update_fields=['status'])

        ReservationStatusHistory.objects.create(
            request=req,
            old_status=old_status,
            new_status=ReservationStatusChoices.PAYMENT_LINK_SENT,
            notes=f"Lien de paiement envoyé par le SuperAdmin {admin_user.email}"
        )

        payment_url = reverse('payment_checkout', kwargs={'booking_id': req.id})
        NotificationService.notify_client(
            req.client,
            "Lien de paiement disponible",
            f"Votre réservation pour « {req.property.title} » est approuvée. "
            f"Veuillez procéder au règlement pour confirmer votre séjour.",
            link=payment_url,
        )

        logger.info(f"Lien de paiement envoyé pour la demande : {req.id}")
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
            
        if req.status != ReservationStatusChoices.SENT_TO_OWNER:
            raise InvalidWorkflowTransition("La demande doit être au statut SENT_TO_OWNER.")

        old_status = req.status
        req.status = ReservationStatusChoices.OWNER_DECLINED
        req.save(update_fields=['status'])

        ReservationStatusHistory.objects.create(
            request=req,
            old_status=old_status,
            new_status=ReservationStatusChoices.OWNER_DECLINED,
            notes=f"Rejetée par le propriétaire {owner.email} : {reason}"
        )
        
        logger.info(f"Demande rejetée par le propriétaire : {req.id}")
        return req

    @staticmethod
    @transaction.atomic
    def confirm_payment(req: ReservationRequest, total_price: Decimal) -> Reservation:
        if req.status not in [ReservationStatusChoices.PAYMENT_PENDING, ReservationStatusChoices.PAYMENT_LINK_SENT]:
            raise InvalidWorkflowTransition("La demande doit être au statut PAYMENT_PENDING ou PAYMENT_LINK_SENT.")
            
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

    @staticmethod
    @transaction.atomic
    def contact_owner(req: ReservationRequest, admin_user: User) -> Reservation:
        """
        Le SuperAdmin confirme le paiement et met le client en contact avec le propriétaire.
        Génère la réservation fermée si elle n'existe pas encore.
        REQUESTED PAYMENT_LINK_SENT -> CONFIRMED + Reservation créée -> OWNER_CONTACTED
        """
        if req.status not in [ReservationStatusChoices.CONFIRMED, ReservationStatusChoices.PAYMENT_LINK_SENT]:
            raise InvalidWorkflowTransition("La demande doit être payée ou confirmée.")

        reservation = Reservation.objects.filter(request=req).first()

        if not reservation:
            from apps.properties.services.services import PropertyService
            total_price = PropertyService.calculate_price_for_stay(req.property, req.check_in, req.check_out)
            reservation = Reservation.objects.create(
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
                reservation=reservation,
                action="Réservation créée par le SuperAdmin",
                details={"admin": admin_user.email}
            )

        old_status = req.status
        req.status = ReservationStatusChoices.OWNER_CONTACTED
        req.save(update_fields=['status'])

        ReservationStatusHistory.objects.create(
            request=req,
            old_status=old_status,
            new_status=ReservationStatusChoices.OWNER_CONTACTED,
            notes=f"Client et propriétaire mis en contact par le SuperAdmin {admin_user.email}"
        )

        NotificationService.notify_client(
            req.client,
            "Réservation confirmée",
            f"Votre réservation pour « {req.property.title} » est confirmée. "
            f"Votre code de confirmation est : {reservation.confirmation_code}. "
            f"Vous pouvez désormais contacter le propriétaire pour organiser votre arrivée.",
            link=reverse('dashboard:client_reservation_detail', kwargs={'pk': reservation.id}),
        )
        NotificationService.notify_owner(
            req.property.owner,
            "Nouvelle réservation confirmée",
            f"Une réservation pour « {req.property.title} » a été confirmée. "
            f"Client : {req.client.email} | Arrivée : {req.check_in.strftime('%d/%m/%Y')} | Départ : {req.check_out.strftime('%d/%m/%Y')}. "
            f"Vous pouvez désormais contacter le client pour organiser l'accueil.",
            link=reverse('dashboard:owner_request_detail', kwargs={'pk': req.id}),
        )

        logger.info(f"Contact établi entre client {req.client.email} et propriétaire {req.property.owner.email} pour la réservation {reservation.confirmation_code}")
        return reservation
