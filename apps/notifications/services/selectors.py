from django.db.models import QuerySet
from apps.notifications.models import Notification, NotificationPreference

class NotificationSelector:

    @staticmethod
    def get_or_create_preferences(user) -> NotificationPreference:
        preferences, _ = NotificationPreference.objects.get_or_create(user=user)
        return preferences

    @staticmethod
    def get_unread_notifications(user_id: str) -> QuerySet[Notification]:
        user = user_id.id if hasattr(user_id, 'id') else user_id
        return Notification.objects.filter(
            user_id=user,
            is_read=False,
            is_deleted=False
        ).order_by('-created_at')

    @staticmethod
    def get_user_notifications(user_id: str) -> QuerySet[Notification]:
        user = user_id.id if hasattr(user_id, 'id') else user_id
        return Notification.objects.filter(
            user_id=user,
            is_deleted=False
        ).order_by('-created_at')

    @staticmethod
    def get_unread_count(user_id: str) -> int:
        user = user_id.id if hasattr(user_id, 'id') else user_id
        return Notification.objects.filter(
            user_id=user,
            is_read=False,
            is_deleted=False
        ).count()
