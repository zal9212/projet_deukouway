from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel
from apps.properties.models import Property
from .choices import ReservationStatusChoices


class ReservationRequest(BaseModel):
    """
    Demande initiale effectuée par un client.
    Le workflow DEKOUWAY impose que cette demande soit traitée par le SuperAdmin,
    qui la transmettra ensuite au propriétaire.
    """
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='reservation_requests', verbose_name=_('Client'))
    property = models.ForeignKey(Property, on_delete=models.PROTECT, related_name='reservation_requests', verbose_name=_('Propriété'))
    
    check_in = models.DateField(_('Date d\'arrivée'))
    check_out = models.DateField(_('Date de départ'))
    guests = models.PositiveIntegerField(_('Nombre de personnes'), validators=[MinValueValidator(1)])
    
    status = models.CharField(
        _('Statut de la demande'),
        max_length=20, 
        choices=ReservationStatusChoices.choices, 
        default=ReservationStatusChoices.REQUESTED,
        db_index=True
    )
    
    special_requests = models.TextField(_('Demandes spéciales'), blank=True)
    superadmin_notes = models.TextField(_('Notes internes (SuperAdmin)'), blank=True, help_text=_("Notes invisibles pour le client et le propriétaire"))

    class Meta(BaseModel.Meta):
        verbose_name = _('Demande de Réservation')
        verbose_name_plural = _('Demandes de Réservation')
        db_table = 'reservations_request'
        constraints = [
            models.CheckConstraint(check=models.Q(check_out__gt=models.F('check_in')), name='check_dates_validity')
        ]

    def __str__(self) -> str:
        return f"Demande {self.id} - {self.client.email} ({self.status})"


class Reservation(BaseModel):
    """
    Réservation ferme et définitive, générée une fois le processus de validation
    et de paiement terminé.
    """
    request = models.OneToOneField(ReservationRequest, on_delete=models.PROTECT, related_name='reservation', verbose_name=_('Demande liée'))
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='reservations', verbose_name=_('Client'))
    property = models.ForeignKey(Property, on_delete=models.PROTECT, related_name='reservations', verbose_name=_('Propriété'))
    
    check_in = models.DateField(_('Date d\'arrivée'))
    check_out = models.DateField(_('Date de départ'))
    guests = models.PositiveIntegerField(_('Nombre de personnes'), validators=[MinValueValidator(1)])
    
    total_price = models.DecimalField(_('Prix total'), max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    
    status = models.CharField(
        _('Statut de la réservation'),
        max_length=20, 
        choices=ReservationStatusChoices.choices, 
        default=ReservationStatusChoices.CONFIRMED,
        db_index=True
    )
    
    confirmation_code = models.CharField(_('Code de confirmation'), max_length=20, unique=True, db_index=True)

    class Meta(BaseModel.Meta):
        verbose_name = _('Réservation')
        verbose_name_plural = _('Réservations')
        db_table = 'reservations_reservation'

    def __str__(self) -> str:
        return f"Réservation {self.confirmation_code} - {self.client.email}"


class ReservationHistory(BaseModel):
    """
    Historique immuable des actions sur une réservation (Check-in, Litige, etc.).
    """
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='history', verbose_name=_('Réservation'))
    action = models.CharField(_('Action'), max_length=255)
    details = models.JSONField(_('Détails'), default=dict)

    class Meta(BaseModel.Meta):
        verbose_name = _('Historique de Réservation')
        verbose_name_plural = _('Historiques de Réservations')
        db_table = 'reservations_history'

    def __str__(self) -> str:
        return f"{self.action} - {self.reservation.confirmation_code}"


class ReservationStatusHistory(BaseModel):
    """
    Historique des changements de statuts du workflow complet.
    """
    request = models.ForeignKey(ReservationRequest, on_delete=models.CASCADE, related_name='status_history', verbose_name=_('Demande'))
    old_status = models.CharField(_('Ancien statut'), max_length=20, choices=ReservationStatusChoices.choices)
    new_status = models.CharField(_('Nouveau statut'), max_length=20, choices=ReservationStatusChoices.choices)
    notes = models.TextField(_('Notes'), blank=True)

    class Meta(BaseModel.Meta):
        verbose_name = _('Historique Statut Demande')
        verbose_name_plural = _('Historiques Statuts Demandes')
        db_table = 'reservations_status_history'

    def __str__(self) -> str:
        return f"{self.request.id}: {self.old_status} -> {self.new_status}"
