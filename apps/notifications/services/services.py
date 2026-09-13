from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone
from apps.accounts.models import User
from apps.notifications.models import Notification, NotificationPreference, NotificationHistory
from apps.core.emails import send_transactional_email
import logging

logger = logging.getLogger(__name__)


class NotificationService:

    @staticmethod
    def get_superadmins():
        """Retourne l'ensemble des SuperAdmin actifs de la plateforme."""
        return User.objects.filter(
            is_active=True,
            is_deleted=False,
        ).filter(
            # Un SuperAdmin est identifié par le rôle explicite, le staff ou le superuser.
        ).filter(is_superadmin=True) | User.objects.filter(
            is_active=True,
            is_deleted=False,
            is_superuser=True,
        )

    @staticmethod
    @transaction.atomic
    def _create_notification(user: User, title: str, message: str, link: str = None,
                             email_template: str = None, email_context: dict = None,
                             email_subject: str = None) -> Notification:
        notif = Notification.objects.create(
            user=user,
            title=title,
            message=message,
            link=link
        )
        logger.info(f"Notification créée pour {user.email} : {title}")

        NotificationService._send_email(
            user=user,
            title=email_subject or title,
            message=message,
            link=link,
            template_name=email_template,
            context=email_context or {},
            notification=notif,
        )
        return notif

    @staticmethod
    def _send_email(user: User, title: str, message: str, link: str = None,
                    template_name: str = None, context: dict = None,
                    notification: Notification = None) -> None:
        """
        Envoie l'email transactionnel si l'utilisateur a activé le canal email.
        Ne fait jamais échouer la transaction métier : tout échec d'envoi est
        journalisé dans l'historique de notification, pas propagé vers l'appelant.
        """
        if not context:
            context = {}

        prefs = None
        try:
            prefs = NotificationPreference.objects.filter(user=user).first()
        except Exception as exc:  # pragma: no cover - défensif
            logger.warning("Impossible de charger les préférences email de %s : %s", user.email, exc)

        if prefs is not None and prefs.email_enabled is False:
            return

        if not getattr(user, 'email', None):
            return

        base_context = {
            'user': user,
            'title': title,
            'message': message,
            'link': link,
        }
        base_context.update(context)

        try:
            sent = send_transactional_email(
                subject=title,
                recipient_email=user.email,
                template_name=template_name or 'emails/generic_notification.html',
                context=base_context,
            )
            if notification is not None:
                NotificationHistory.objects.create(
                    notification=notification,
                    channel='EMAIL',
                    status='SENT' if sent else 'FAILED',
                    error_message='' if sent else "Envoi échoué (voir logs email).",
                )
        except Exception as exc:  # pragma: no cover - défensif
            logger.error("Échec tracking email pour %s : %s", user.email, exc, exc_info=True)
            if notification is not None:
                try:
                    NotificationHistory.objects.create(
                        notification=notification,
                        channel='EMAIL',
                        status='FAILED',
                        error_message=str(exc),
                    )
                except Exception:  # pragma: no cover
                    pass

    @staticmethod
    @transaction.atomic
    def notify_client(client: User, title: str, message: str, link: str = None,
                      email_template: str = None, email_context: dict = None,
                      email_subject: str = None) -> Notification:
        return NotificationService._create_notification(
            client, title, message, link,
            email_template=email_template, email_context=email_context, email_subject=email_subject,
        )

    @staticmethod
    @transaction.atomic
    def notify_owner(owner: User, title: str, message: str, link: str = None,
                     email_template: str = None, email_context: dict = None,
                     email_subject: str = None) -> Notification:
        return NotificationService._create_notification(
            owner, title, message, link,
            email_template=email_template, email_context=email_context, email_subject=email_subject,
        )

    @staticmethod
    @transaction.atomic
    def notify_admin(admin: User, title: str, message: str, link: str = None,
                     email_template: str = None, email_context: dict = None,
                     email_subject: str = None) -> Notification:
        return NotificationService._create_notification(
            admin, title, message, link,
            email_template=email_template, email_context=email_context, email_subject=email_subject,
        )

    @staticmethod
    @transaction.atomic
    def notify_all_admins(title: str, message: str, link: str = None,
                          email_template: str = None, email_context: dict = None,
                          email_subject: str = None) -> list:
        """Notifie (in-app + email) tous les SuperAdmin actifs de la plateforme."""
        admins = NotificationService.get_superadmins().distinct()
        notifications = []
        for admin in admins:
            try:
                notif = NotificationService._create_notification(
                    admin, title, message, link,
                    email_template=email_template,
                    email_context=email_context,
                    email_subject=email_subject,
                )
                notifications.append(notif)
            except Exception as exc:  # pragma: no cover - défensif
                logger.error("Échec notification admin %s : %s", admin.email, exc, exc_info=True)
        return notifications

    @staticmethod
    @transaction.atomic
    def mark_as_read(notification: Notification) -> Notification:
        if notification.is_read:
            pass # Ou lever une exception

        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=['is_read', 'read_at'])
        return notification

    @staticmethod
    @transaction.atomic
    def mark_all_as_read(user: User) -> None:
        Notification.objects.filter(user=user, is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )

    @staticmethod
    @transaction.atomic
    def broadcast(title: str, message: str, link: str = None) -> None:
        """Envoie une notification à tous les utilisateurs actifs."""
        users = User.objects.filter(is_active=True, is_deleted=False)
        notifications = [
            Notification(user=u, title=title, message=message, link=link) for u in users
        ]
        Notification.objects.bulk_create(notifications)
        logger.info(f"Notification diffusée : {title}")

    @staticmethod
    @transaction.atomic
    def create_system_notification(user: User, title: str, message: str) -> Notification:
        return NotificationService._create_notification(user, f"[SYSTÈME] {title}", message)

    @staticmethod
    @transaction.atomic
    def update_preferences(user: User, email_enabled: bool, sms_enabled: bool) -> NotificationPreference:
        preferences, _ = NotificationPreference.objects.get_or_create(user=user)
        preferences.email_enabled = email_enabled
        preferences.sms_enabled = sms_enabled
        preferences.save(update_fields=['email_enabled', 'sms_enabled'])
        return preferences
