from django.db import models
from django.utils.translation import gettext_lazy as _

class PropertyStatusChoices(models.TextChoices):
    DRAFT = 'DRAFT', _('Brouillon')
    PENDING = 'PENDING', _('En attente')
    UNDER_REVIEW = 'UNDER_REVIEW', _('En cours de révision')
    APPROVED = 'APPROVED', _('Approuvé')
    REJECTED = 'REJECTED', _('Rejeté')
    PUBLISHED = 'PUBLISHED', _('Publié')
    SUSPENDED = 'SUSPENDED', _('Suspendu')
    ARCHIVED = 'ARCHIVED', _('Archivé')
