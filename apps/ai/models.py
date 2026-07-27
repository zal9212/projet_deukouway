from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel
from apps.ai.choices import ConversationRoleChoices, AIModeChoices

class Conversation(BaseModel):
    """
    Historique d'une session de conversation avec le Chatbot DEKOUWAY.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ai_conversations', verbose_name=_('Utilisateur'))
    mode = models.CharField(_('Mode IA'), max_length=30, choices=AIModeChoices.choices, default=AIModeChoices.GENERAL_CHAT)
    title = models.CharField(_('Titre de la conversation'), max_length=255, default='Nouvelle conversation')

    class Meta(BaseModel.Meta):
        verbose_name = _('Conversation IA')
        verbose_name_plural = _('Conversations IA')
        db_table = 'ai_conversation'

    def __str__(self) -> str:
        return f"Conversation {self.id} - {self.user.email} ({self.mode})"


class ConversationMessage(BaseModel):
    """
    Message individuel au sein d'une conversation IA.
    """
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages', verbose_name=_('Conversation'))
    role = models.CharField(_('Rôle'), max_length=20, choices=ConversationRoleChoices.choices)
    content = models.TextField(_('Contenu du message'))
    tokens_used = models.PositiveIntegerField(_('Nombre de jetons'), default=0)
    latency_ms = models.FloatField(_('Durée (ms)'), default=0.0)

    class Meta(BaseModel.Meta):
        verbose_name = _('Message IA')
        verbose_name_plural = _('Messages IA')
        db_table = 'ai_conversation_message'
        ordering = ['created_at']

    def __str__(self) -> str:
        return f"[{self.role}] {self.content[:30]}..."


class AIUsageLog(BaseModel):
    """
    Journal d'audit des appels à l'API Groq (gestion des quotas, temps de réponse et coûts).
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('Utilisateur'))
    feature = models.CharField(_('Fonctionnalité IA'), max_length=50) # ex: CHAT, MODERATION, RECOMMENDATION
    model_name = models.CharField(_('Modèle utilisé'), max_length=100)
    prompt_tokens = models.PositiveIntegerField(_('Jetons Prompt'), default=0)
    completion_tokens = models.PositiveIntegerField(_('Jetons Génération'), default=0)
    total_tokens = models.PositiveIntegerField(_('Total Jetons'), default=0)
    execution_time_sec = models.FloatField(_('Temps d\'exécution (s)'), default=0.0)
    is_success = models.BooleanField(_('Succès'), default=True)
    fallback_used = models.BooleanField(_('Moteur de secours utilisé'), default=False)

    class Meta(BaseModel.Meta):
        verbose_name = _('Journal d\'Usage IA')
        verbose_name_plural = _('Journaux d\'Usage IA')
        db_table = 'ai_usage_log'

    def __str__(self) -> str:
        return f"Log IA {self.feature} - {self.total_tokens} tokens ({self.created_at})"
