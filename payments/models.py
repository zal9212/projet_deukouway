from django.db import models
from bookings.models import Booking
import uuid

class Payment(models.Model):
    """
    Payment transaction logs tracking payments for bookings.
    """
    METHOD_CHOICES = (
        ('card', 'Carte Bancaire (Visa/Mastercard)'),
        ('wave', 'Wave'),
        ('orange_money', 'Orange Money'),
    )

    STATUS_CHOICES = (
        ('pending', 'En attente'),
        ('completed', 'Réussi'),
        ('failed', 'Échoué'),
    )

    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name='payment'
    )
    
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        verbose_name="Montant payé (FCFA)"
    )
    
    payment_method = models.CharField(
        max_length=20,
        choices=METHOD_CHOICES,
        verbose_name="Moyen de paiement"
    )
    
    transaction_id = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="ID de transaction"
    )
    
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Statut du paiement"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # Auto generate transaction ID if missing
        if not self.transaction_id:
            self.transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Payment {self.transaction_id} of {self.amount} F for Booking {self.booking_id}"
