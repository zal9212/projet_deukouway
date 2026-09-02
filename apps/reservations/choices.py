from django.db import models
from django.utils.translation import gettext_lazy as _

class ReservationStatusChoices(models.TextChoices):
    REQUESTED = 'REQUESTED', _('Demandé')
    UNDER_REVIEW = 'UNDER_REVIEW', _('En cours de révision (SuperAdmin)')
    SENT_TO_OWNER = 'SENT_TO_OWNER', _('Transmis au Propriétaire')
    OWNER_ACCEPTED = 'OWNER_ACCEPTED', _('Accepté par le Propriétaire')
    OWNER_DECLINED = 'OWNER_DECLINED', _('Refusé par le Propriétaire')
    REJECTED = 'REJECTED', _('Rejeté par DEKOUWAY')
    PAYMENT_PENDING = 'PAYMENT_PENDING', _('En attente de paiement')
    PAYMENT_LINK_SENT = 'PAYMENT_LINK_SENT', _('Lien de paiement envoyé')
    PAID = 'PAID', _('Payé')
    CONFIRMED = 'CONFIRMED', _('Confirmé')
    OWNER_CONTACTED = 'OWNER_CONTACTED', _('Propriétaire contacté')
    CHECKIN = 'CHECKIN', _('Check-in')
    CHECKOUT = 'CHECKOUT', _('Check-out')
    COMPLETED = 'COMPLETED', _('Terminé')
    CANCELLED = 'CANCELLED', _('Annulé')
