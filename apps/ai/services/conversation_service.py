from django.db import transaction
from typing import List, Dict
from apps.accounts.models import User
from apps.ai.models import Conversation, ConversationMessage
from apps.ai.choices import ConversationRoleChoices, AIModeChoices
import logging

logger = logging.getLogger(__name__)

class ConversationService:
    """
    Service de gestion et d'archivage des conversations IA.
    """

    @classmethod
    @transaction.atomic
    def get_or_create_conversation(cls, user: User, mode: str = AIModeChoices.GENERAL_CHAT, title: str = None) -> Conversation:
        conv = Conversation.objects.filter(user=user, mode=mode, is_deleted=False).order_by('-created_at').first()
        if not conv:
            conv = Conversation.objects.create(
                user=user,
                mode=mode,
                title=title or f"Discussion {mode}"
            )
            logger.info(f"Nouvelle session de conversation IA créée : {conv.id} ({mode}) pour {user.email}")
        return conv

    @classmethod
    @transaction.atomic
    def record_message(cls, conversation: Conversation, role: str, content: str, tokens: int = 0, latency_ms: float = 0.0) -> ConversationMessage:
        return ConversationMessage.objects.create(
            conversation=conversation,
            role=role,
            content=content,
            tokens_used=tokens,
            latency_ms=latency_ms
        )

    @classmethod
    @transaction.atomic
    def clear_user_history(cls, user: User, mode: str = None) -> None:
        qs = Conversation.objects.filter(user=user, is_deleted=False)
        if mode:
            qs = qs.filter(mode=mode)
        
        for conv in qs:
            conv.soft_delete()
        logger.info(f"Historique de conversation IA effacé pour {user.email}")
