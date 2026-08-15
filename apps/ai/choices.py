from django.db import models
from django.utils.translation import gettext_lazy as _

class ConversationRoleChoices(models.TextChoices):
    SYSTEM = 'SYSTEM', _('Système')
    USER = 'USER', _('Utilisateur')
    ASSISTANT = 'ASSISTANT', _('Assistant IA')


class AIModeChoices(models.TextChoices):
    GENERAL_CHAT = 'GENERAL_CHAT', _('Discussion Générale')
    CLIENT_ASSISTANT = 'CLIENT_ASSISTANT', _('Assistant Client')
    OWNER_ASSISTANT = 'OWNER_ASSISTANT', _('Assistant Propriétaire')
    ERP_ADMIN_ASSISTANT = 'ERP_ADMIN_ASSISTANT', _('Assistant SuperAdmin ERP')
    RECOMMENDATION = 'RECOMMENDATION', _('Moteur de Recommandation')
    MODERATION = 'MODERATION', _('Modération de Contenu')
    DESCRIPTION_GEN = 'DESCRIPTION_GEN', _('Génération de Description')
