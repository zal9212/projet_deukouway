from django.db import models
from django.utils.translation import gettext_lazy as _

class TicketStatusChoices(models.TextChoices):
    OPEN = 'OPEN', _('Ouvert')
    IN_PROGRESS = 'IN_PROGRESS', _('En cours')
    RESOLVED = 'RESOLVED', _('Résolu')
    CLOSED = 'CLOSED', _('Fermé')

class DisputeStatusChoices(models.TextChoices):
    OPEN = 'OPEN', _('Ouvert')
    UNDER_INVESTIGATION = 'UNDER_INVESTIGATION', _('En cours d\'investigation')
    RESOLVED_CLIENT = 'RESOLVED_CLIENT', _('Résolu en faveur du Client')
    RESOLVED_OWNER = 'RESOLVED_OWNER', _('Résolu en faveur du Propriétaire')
    RESOLVED_SPLIT = 'RESOLVED_SPLIT', _('Résolution partagée')
