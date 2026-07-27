from django.db import transaction
from django.utils import timezone
from apps.accounts.models import User
from apps.notifications.models import Notification, NotificationHistory, NotificationPreference
import logging

logger = logging.getLogger(__name__)

class NotificationService:

    @staticmethod
    @transaction.atomic
    def _create_notification(user: User, title: str, message: str, link: str = None) -> Notification:
        notif = Notification.objects.create(
            user=user,
            title=title,
            message=message,
            link=link
        )
        logger.info(f"Notification créée pour {user.email} : {title}")
        return notif

    @staticmethod
    @transaction.atomic
    def notify_client(client: User, title: str, message: str, link: str = None) -> Notification:
        return NotificationService._create_notification(client, title, message, link)

    @staticmethod
    @transaction.atomic
    def notify_owner(owner: User, title: str, message: str, link: str = None) -> Notification:
        return NotificationService._create_notification(owner, title, message, link)

    @staticmethod
    @transaction.atomic
    def notify_admin(admin: User, title: str, message: str, link: str = None) -> Notification:
        return NotificationService._create_notification(admin, title, message, link)

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
