from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel
from apps.reservations.models import Reservation
from .choices import PaymentMethodChoices, PaymentStatusChoices, PayoutStatusChoices


class Payment(BaseModel):
    """
    Paiement entrant (d'un Client vers DEKOUWAY).
    Ce paiement est isolé et tracé indépendamment de la commission et du reversement.
    """
    reservation = models.ForeignKey(Reservation, on_delete=models.PROTECT, related_name='payments', verbose_name=_('Réservation'))
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='payments_made', verbose_name=_('Utilisateur'))
    
    amount = models.DecimalField(_('Montant'), max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    currency = models.CharField(_('Devise'), max_length=3, default='XOF')
    
    method = models.CharField(_('Méthode de paiement'), max_length=20, choices=PaymentMethodChoices.choices)
    status = models.CharField(
        _('Statut'),
        max_length=20, 
        choices=PaymentStatusChoices.choices, 
        default=PaymentStatusChoices.PENDING, 
        db_index=True
    )
    
    gateway_transaction_id = models.CharField(_('ID Transaction (Gateway)'), max_length=255, blank=True, null=True, db_index=True)
    error_message = models.TextField(_('Message d\'erreur'), blank=True)

    class Meta(BaseModel.Meta):
        verbose_name = _('Paiement Entrant')
        verbose_name_plural = _('Paiements Entrants')
        db_table = 'payments_payment'

    def __str__(self) -> str:
        return f"Paiement {self.id} - {self.amount} {self.currency} ({self.status})"


class Commission(BaseModel):
    """
    La marge financière prélevée par DEKOUWAY sur un paiement réussi.
    """
    payment = models.OneToOneField(Payment, on_delete=models.PROTECT, related_name='commission', verbose_name=_('Paiement associé'))
    percentage_applied = models.DecimalField(_('Pourcentage appliqué (%)'), max_digits=5, decimal_places=2, help_text="ex: 15.00 pour 15%", validators=[MinValueValidator(0.00)])
    amount = models.DecimalField(_('Montant de la commission'), max_digits=12, decimal_places=2, validators=[MinValueValidator(0.00)])
    service_fee = models.DecimalField(_('Frais de service (Fixe)'), max_digits=12, decimal_places=2, default=0.00, validators=[MinValueValidator(0.00)])
    
    class Meta(BaseModel.Meta):
        verbose_name = _('Commission DEKOUWAY')
        verbose_name_plural = _('Commissions DEKOUWAY')
        db_table = 'payments_commission'

    def __str__(self) -> str:
        return f"Commission pour Paiement {self.payment.id} - {self.amount}"


class Payout(BaseModel):
    """
    Reversement financier sortant de DEKOUWAY vers le Propriétaire, validé par SuperAdmin.
    """
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='payouts_received', verbose_name=_('Propriétaire'))
    reservation = models.ForeignKey(Reservation, on_delete=models.PROTECT, related_name='payouts', verbose_name=_('Réservation'))
    
    amount = models.DecimalField(_('Montant reversé'), max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    currency = models.CharField(_('Devise'), max_length=3, default='XOF')
    
    method = models.CharField(_('Méthode de reversement'), max_length=20, choices=PaymentMethodChoices.choices)
    status = models.CharField(
        _('Statut'),
        max_length=20, 
        choices=PayoutStatusChoices.choices, 
        default=PayoutStatusChoices.PENDING, 
        db_index=True
    )
    
    gateway_transaction_id = models.CharField(_('ID Transaction Reversement'), max_length=255, blank=True, null=True, db_index=True)

    class Meta(BaseModel.Meta):
        verbose_name = _('Reversement Propriétaire')
        verbose_name_plural = _('Reversements Propriétaires')
        db_table = 'payments_payout'

    def __str__(self) -> str:
        return f"Reversement {self.id} - {self.amount} {self.currency} ({self.status})"


class Invoice(BaseModel):
    """
    Facture légale générée automatiquement et stockée de façon immuable.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='invoices', verbose_name=_('Utilisateur'))
    reservation = models.ForeignKey(Reservation, on_delete=models.PROTECT, related_name='invoices', verbose_name=_('Réservation'))
    invoice_number = models.CharField(_('Numéro de facture'), max_length=50, unique=True, db_index=True)
    file = models.FileField(
        _('Fichier Facture (PDF)'), 
        upload_to='invoices/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])]
    )
    
    class Meta(BaseModel.Meta):
        verbose_name = _('Facture')
        verbose_name_plural = _('Factures')
        db_table = 'payments_invoice'

    def __str__(self) -> str:
        return f"Facture {self.invoice_number}"


class Refund(BaseModel):
    """
    Remboursement suite à une annulation ou un litige.
    """
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name='refunds', verbose_name=_('Paiement d\'origine'))
    amount = models.DecimalField(_('Montant'), max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    reason = models.TextField(_('Motif du remboursement'))
    status = models.CharField(_('Statut'), max_length=20, choices=PaymentStatusChoices.choices, default=PaymentStatusChoices.PENDING)
    gateway_transaction_id = models.CharField(_('ID Transaction (Gateway)'), max_length=255, blank=True, null=True)

    class Meta(BaseModel.Meta):
        verbose_name = _('Remboursement')
        verbose_name_plural = _('Remboursements')
        db_table = 'payments_refund'

    def __str__(self) -> str:
        return f"Remboursement {self.id} - {self.amount} ({self.status})"


class PaymentHistory(BaseModel):
    """
    Historique d'audit des flux de paiements.
    """
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='history', verbose_name=_('Paiement'))
    old_status = models.CharField(_('Ancien statut'), max_length=20, choices=PaymentStatusChoices.choices)
    new_status = models.CharField(_('Nouveau statut'), max_length=20, choices=PaymentStatusChoices.choices)
    details = models.JSONField(_('Détails'), default=dict)

    class Meta(BaseModel.Meta):
        verbose_name = _('Historique de Paiement')
        verbose_name_plural = _('Historiques de Paiements')
        db_table = 'payments_history'

    def __str__(self) -> str:
        return f"{self.payment.id}: {self.old_status} -> {self.new_status}"


class PlatformSettings(BaseModel):
    """
    Règles financières globales de la plateforme DEKOUWAY (singleton).
    """
    commission_percentage = models.DecimalField(
        _('Commission Propriétaire (%)'),
        max_digits=5, decimal_places=2, default=Decimal('15.00'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))]
    )
    client_service_fee = models.DecimalField(
        _('Frais de service Client (Fixe en FCFA)'),
        max_digits=12, decimal_places=2, default=Decimal('5000.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    class Meta(BaseModel.Meta):
        verbose_name = _('Configuration de la Plateforme')
        verbose_name_plural = _('Configuration de la Plateforme')
        db_table = 'payments_platform_settings'

    def __str__(self) -> str:
        return f"Configuration Plateforme (Commission {self.commission_percentage}%)"

    @classmethod
    def load(cls) -> 'PlatformSettings':
        obj = cls.objects.filter(is_deleted=False).order_by('created_at').first()
        if not obj:
            obj = cls.objects.create()
        return obj
