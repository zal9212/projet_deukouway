from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from properties.models import Property

class Booking(models.Model):
    """
    Booking records managing dates, total price, and multi-state status.
    """
    STATUS_CHOICES = (
        ('pending', 'En attente de validation'),
        ('approved', 'Acceptée (En attente de paiement)'),
        ('confirmed', 'Confirmée (Payée)'),
        ('rejected', 'Refusée'),
        ('cancelled', 'Annulée'),
    )

    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings',
        limit_choices_to={'role': 'client'}
    )
    check_in = models.DateField(verbose_name="Date d'arrivée")
    check_out = models.DateField(verbose_name="Date de départ")
    
    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        verbose_name="Prix total (FCFA)"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Statut de la réservation"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Réservation"
        verbose_name_plural = "Réservations"
        ordering = ['-created_at']

    def clean(self):
        super().clean()
        if self.check_in and self.check_out:
            if self.check_in >= self.check_out:
                raise ValidationError("La date d'arrivée doit être antérieure à la date de départ.")
            
            # Check for overlapping bookings (approved or confirmed)
            overlapping = Booking.objects.filter(
                property=self.property,
                status__in=['approved', 'confirmed'],
                check_in__lt=self.check_out,
                check_out__gt=self.check_in
            )
            if self.pk:
                overlapping = overlapping.exclude(pk=self.pk)
                
            if overlapping.exists():
                raise ValidationError("Ce logement est déjà réservé pour ces dates.")

    def save(self, *args, **kwargs):
        self.clean()
        # Automatically calculate price
        if not self.total_price and self.check_in and self.check_out:
            days = (self.check_out - self.check_in).days
            self.total_price = days * self.property.price_per_night
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Booking {self.id} for {self.property.title} by {self.client.first_name}"
