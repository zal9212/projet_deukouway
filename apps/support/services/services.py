from django.db import transaction
from apps.accounts.models import User
from apps.support.models import Ticket, TicketMessage, SupportCategory, ContactMessage
from apps.support.services.exceptions import TicketAlreadyClosed, UnauthorizedTicketAction
import logging

logger = logging.getLogger(__name__)

class SupportService:

    @staticmethod
    @transaction.atomic
    def submit_contact_message(name: str, email: str, subject: str, message: str, user: User = None) -> ContactMessage:
        contact_message = ContactMessage.objects.create(
            name=name,
            email=email,
            subject=subject,
            message=message,
            user=user if (user and user.is_authenticated) else None,
        )
        logger.info(f"Message de contact reçu de {email} : {subject}")
        return contact_message

    @staticmethod
    @transaction.atomic
    def create_ticket(user: User, category: SupportCategory, subject: str, description: str) -> Ticket:
        ticket = Ticket.objects.create(
            user=user,
            category=category,
            subject=subject,
            description=description,
            status='OPEN'
        )
        logger.info(f"Ticket créé : {ticket.id} par {user.email}")
        return ticket

    @staticmethod
    @transaction.atomic
    def reply_ticket(ticket: Ticket, sender: User, content: str, is_internal: bool = False) -> TicketMessage:
        if ticket.status == 'CLOSED':
            raise TicketAlreadyClosed("Impossible de répondre à un ticket fermé.")
            
        message = TicketMessage.objects.create(
            ticket=ticket,
            sender=sender,
            content=content,
            is_internal=is_internal
        )
        
        # Mettre à jour le statut du ticket si un admin répond
        if getattr(sender, 'is_superadmin', False) or sender.is_superuser or sender.is_staff:
            ticket.status = 'IN_PROGRESS'
            ticket.save(update_fields=['status'])
            
        logger.info(f"Réponse ajoutée au ticket : {ticket.id} par {sender.email}")
        return message

    add_message_to_ticket = reply_ticket

    @staticmethod
    @transaction.atomic
    def close_ticket(ticket: Ticket, user: User) -> Ticket:
        if ticket.status == 'CLOSED':
            raise TicketAlreadyClosed("Le ticket est déjà fermé.")
            
        # Seulement l'auteur ou un admin peut fermer
        if ticket.user_id != user.id and not (getattr(user, 'is_superadmin', False) or user.is_superuser or user.is_staff):
            raise UnauthorizedTicketAction("Vous n'êtes pas autorisé à fermer ce ticket.")
            
        ticket.status = 'CLOSED'
        ticket.save(update_fields=['status'])
        logger.info(f"Ticket fermé : {ticket.id} par {user.email}")
        return ticket

    @staticmethod
    @transaction.atomic
    def assign_admin(ticket: Ticket, admin_user: User) -> Ticket:
        if ticket.status == 'CLOSED':
            raise TicketAlreadyClosed("Impossible d'assigner un ticket fermé.")
            
        ticket.assigned_to = admin_user
        ticket.status = 'IN_PROGRESS'
        ticket.save(update_fields=['assigned_to', 'status'])
        
        logger.info(f"Ticket {ticket.id} assigné à {admin_user.email}")
        return ticket

    @staticmethod
    @transaction.atomic
    def escalate(ticket: Ticket, admin_user: User) -> Ticket:
        if ticket.status == 'CLOSED':
            raise TicketAlreadyClosed("Impossible d'escalader un ticket fermé.")
            
        ticket.status = 'ESCALATED'
        ticket.save(update_fields=['status'])
        
        logger.warning(f"Ticket {ticket.id} escaladé par {admin_user.email}")
        return ticket
