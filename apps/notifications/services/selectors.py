from django.db.models import QuerySet
from apps.notifications.models import Notification

class NotificationSelector:
    
    @staticmethod
    def get_unread_notifications(user_id: str) -> QuerySet[Notification]:
        return Notification.objects.filter(
            user_id=user_id,
            is_read=False,
            is_deleted=False
        ).order_by('-created_at')
