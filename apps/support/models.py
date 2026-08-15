from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel
from apps.reservations.models import Reservation
from apps.properties.models import Property
from .choices import TicketStatusChoices, DisputeStatusChoices


class SupportCategory(BaseModel):
    """
    Catégories pour le support client/propriétaire (ex: Technique, Facturation).
    """
    name = models.CharField(_('Nom'), max_length=100)
    slug = models.SlugField(_('Slug'), unique=True)
    description = models.TextField(_('Description'), blank=True)

    class Meta(BaseModel.Meta):
        verbose_name = _('Catégorie de Support')
        verbose_name_plural = _('Catégories de Support')
        db_table = 'support_category'

    def __str__(self) -> str:
        return str(self.name)


class ContactMessage(BaseModel):
    """
    Message envoyé depuis le formulaire de contact public (visiteur anonyme ou connecté).
    """
    name = models.CharField(_('Nom'), max_length=150)
    email = models.EmailField(_('Email'))
    subject = models.CharField(_('Sujet'), max_length=255)
    message = models.TextField(_('Message'))
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='contact_messages', verbose_name=_('Utilisateur (si connecté)')
    )
    is_processed = models.BooleanField(_('Traité'), default=False)

    class Meta(BaseModel.Meta):
        verbose_name = _('Message de Contact')
        verbose_name_plural = _('Messages de Contact')
        db_table = 'support_contact_message'

    def __str__(self) -> str:
        return f"{self.subject} - {self.name} ({self.email})"


class Ticket(BaseModel):
    """
    Ticket de support standard (Demande d'aide, question).
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tickets', verbose_name=_('Utilisateur'))
    category = models.ForeignKey(SupportCategory, on_delete=models.PROTECT, verbose_name=_('Catégorie'))
    subject = models.CharField(_('Sujet'), max_length=255)
    description = models.TextField(_('Description'))
    status = models.CharField(
        _('Statut'),
        max_length=20, 
        choices=TicketStatusChoices.choices, 
        default=TicketStatusChoices.OPEN, 
        db_index=True
    )
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='assigned_tickets', verbose_name=_('Assigné à (SuperAdmin)'))

    class Meta(BaseModel.Meta):
        verbose_name = _('Ticket de Support')
        verbose_name_plural = _('Tickets de Support')
        db_table = 'support_ticket'

    def __str__(self) -> str:
        return f"Ticket {self.id} - {self.subject}"


class TicketMessage(BaseModel):
    """
    Messages échangés à l'intérieur d'un ticket.
    Possibilité pour le SuperAdmin de laisser des notes internes (is_internal=True).
    """
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='messages', verbose_name=_('Ticket'))
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ticket_messages', verbose_name=_('Expéditeur'))
    content = models.TextField(_('Contenu du message'))
    is_internal = models.BooleanField(_('Message interne (SuperAdmin)'), default=False, help_text="Visible uniquement par les SuperAdmins")

    class Meta(BaseModel.Meta):
        verbose_name = _('Message de Ticket')
        verbose_name_plural = _('Messages de Tickets')
        db_table = 'support_ticket_message'

    def __str__(self) -> str:
        return f"Message sur Ticket {self.ticket.id} par {self.sender.email}"


class Complaint(BaseModel):
    """
    Plainte relative au comportement (bruit, saleté) d'un client ou d'un propriétaire.
    """
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='complaints_made', verbose_name=_('Auteur de la plainte'))
    target_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='complaints_received', verbose_name=_('Utilisateur signalé'))
    target_property = models.ForeignKey(Property, on_delete=models.PROTECT, null=True, blank=True, related_name='complaints', verbose_name=_('Propriété signalée'))
    reservation = models.ForeignKey(Reservation, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('Réservation (Optionnelle)'))
    
    reason = models.CharField(_('Motif de la plainte'), max_length=255)
    description = models.TextField(_('Description détaillée'))
    status = models.CharField(_('Statut'), max_length=20, choices=TicketStatusChoices.choices, default=TicketStatusChoices.OPEN)

    class Meta(BaseModel.Meta):
        verbose_name = _('Plainte')
        verbose_name_plural = _('Plaintes')
        db_table = 'support_complaint'

    def __str__(self) -> str:
        return f"Plainte {self.id} par {self.author.email}"


class Dispute(BaseModel):
    """
    Litige financier ou critique bloquant une transaction (Caution, Dégradation).
    Requiert l'intervention du SuperAdmin comme médiateur.
    """
    reservation = models.ForeignKey(Reservation, on_delete=models.PROTECT, related_name='disputes', verbose_name=_('Réservation'))
    raised_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='disputes_raised', verbose_name=_('Ouvert par'))
    
    reason = models.CharField(_('Motif du litige'), max_length=255)
    description = models.TextField(_('Description détaillée'))
    
    status = models.CharField(
        _('Statut'),
        max_length=25, 
        choices=DisputeStatusChoices.choices, 
        default=DisputeStatusChoices.OPEN, 
        db_index=True
    )
    resolution_notes = models.TextField(_('Notes de résolution'), blank=True, help_text="Décision finale du SuperAdmin")
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='resolved_disputes', verbose_name=_('Résolu par (SuperAdmin)'))

    class Meta(BaseModel.Meta):
        verbose_name = _('Litige')
        verbose_name_plural = _('Litiges')
        db_table = 'support_dispute'

    def __str__(self) -> str:
        return f"Litige {self.id} sur Réservation {self.reservation.confirmation_code}"
