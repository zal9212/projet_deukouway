from django.db.models import QuerySet
from apps.ai.models import Conversation, AIUsageLog

class AIConversationSelector:
    """
    Sélecteur pour la consultation optimisée des conversations et journaux IA.
    """

    @staticmethod
    def get_user_conversations(user_id: str) -> QuerySet[Conversation]:
        user = user_id.id if hasattr(user_id, 'id') else user_id
        return Conversation.objects.filter(user_id=user, is_deleted=False).prefetch_related('messages').order_by('-created_at')

    @staticmethod
    def get_conversation_by_id(conversation_id: str, user_id: str = None) -> Conversation | None:
        qs = Conversation.objects.filter(id=conversation_id, is_deleted=False).prefetch_related('messages')
        if user_id:
            user = user_id.id if hasattr(user_id, 'id') else user_id
            qs = qs.filter(user_id=user)
        return qs.first()

    @staticmethod
    def get_usage_logs(limit: int = 50) -> QuerySet[AIUsageLog]:
        return AIUsageLog.objects.select_related('user').order_by('-created_at')[:limit]
