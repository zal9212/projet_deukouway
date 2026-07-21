from django.db import models
from django.utils.translation import gettext_lazy as _

class PaymentMethodChoices(models.TextChoices):
    WAVE = 'WAVE', _('Wave')
    ORANGE_MONEY = 'ORANGE_MONEY', _('Orange Money')
    CREDIT_CARD = 'CREDIT_CARD', _('Carte Bancaire')
    BANK_TRANSFER = 'BANK_TRANSFER', _('Virement Bancaire')

class PaymentStatusChoices(models.TextChoices):
    PENDING = 'PENDING', _('En attente')
    SUCCESS = 'SUCCESS', _('Réussi')
    FAILED = 'FAILED', _('Échoué')
    REFUNDED = 'REFUNDED', _('Remboursé')

class PayoutStatusChoices(models.TextChoices):
    PENDING = 'PENDING', _('En attente de reversement')
    PROCESSING = 'PROCESSING', _('En cours de traitement')
    COMPLETED = 'COMPLETED', _('Versé')
    FAILED = 'FAILED', _('Échec')
