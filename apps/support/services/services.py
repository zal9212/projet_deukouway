from django.db import transaction
from django.urls import reverse
from apps.accounts.models import User
from apps.support.models import Ticket, TicketMessage, SupportCategory, ContactMessage
from apps.support.services.exceptions import TicketAlreadyClosed, UnauthorizedTicketAction
import logging

logger = logging.getLogger(__name__)

class SupportService:

    @staticmethod
    def _moderate_and_flag(text: str, on_flagged) -> None:
        """
        Modération automatique best-effort : un échec de l'appel IA ne doit jamais
        empêcher l'envoi d'un message de contact ou d'une réponse de ticket.
        """
        try:
            from apps.ai.services.moderation_service import ModerationService
            result = ModerationService.moderate_text(text)
            if result.get('flagged'):
                on_flagged(result.get('reason', ''))
        except Exception as e:
            logger.error(f"Modération IA indisponible, message laissé non signalé : {e}")

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

        def _flag(reason):
            contact_message.is_flagged = True
            contact_message.moderation_reason = reason
            contact_message.save(update_fields=['is_flagged', 'moderation_reason'])
            logger.warning(f"Message de contact signalé par la modération IA : {contact_message.id} ({reason})")
            from apps.notifications.services.services import NotificationService
            NotificationService.notify_all_admins(
                title="Message de contact signalé par la modération IA",
                message=f"Le message de {email} (« {subject} ») a été signalé : {reason}",
                email_template='emails/generic_notification.html',
            )

        SupportService._moderate_and_flag(message, _flag)
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

        is_admin_sender = getattr(sender, 'is_superadmin', False) or sender.is_superuser or sender.is_staff

        # Mettre à jour le statut du ticket si un admin répond
        if is_admin_sender:
            ticket.status = 'IN_PROGRESS'
            ticket.save(update_fields=['status'])

        # Modération automatique des messages client/propriétaire uniquement (pas les
        # réponses internes de l'équipe) : signale sans jamais bloquer l'envoi.
        if not is_admin_sender and not is_internal:
            def _flag(reason):
                message.is_flagged = True
                message.moderation_reason = reason
                message.save(update_fields=['is_flagged', 'moderation_reason'])
                logger.warning(f"Message de ticket signalé par la modération IA : {message.id} ({reason})")
                from apps.notifications.services.services import NotificationService
                NotificationService.notify_all_admins(
                    title="Message de ticket signalé par la modération IA",
                    message=f"Un message de {sender.email} sur le ticket « {ticket.subject} » a été signalé : {reason}",
                    link=reverse('dashboard:admin_support') + f"?ticket={ticket.id}",
                    email_template='emails/generic_notification.html',
                )
            SupportService._moderate_and_flag(content, _flag)

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
