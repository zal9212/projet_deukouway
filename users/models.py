from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Custom User model for DEKOUWAY supporting roles and profile fields.
    """
    ROLE_CHOICES = (
        ('client', 'Client'),
        ('owner', 'Propriétaire'),
        ('admin', 'Administrateur'),
    )

    OWNER_STATUS_CHOICES = (
        ('pending', 'En attente de validation'),
        ('approved', 'Validé'),
        ('rejected', 'Rejeté'),
    )

    role = models.CharField(
        max_length=15,
        choices=ROLE_CHOICES,
        default='client',
        help_text="Rôle de l'utilisateur sur la plateforme"
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Numéro de téléphone (ex: +221770000000)"
    )

    avatar = models.FileField(
        upload_to='avatars/',
        blank=True,
        null=True,
        help_text="Photo de profil"
    )

    # Specific fields for Owner validation by SuperAdmin
    owner_status = models.CharField(
        max_length=15,
        choices=OWNER_STATUS_CHOICES,
        default='approved',  # Clients are automatically approved
        help_text="Statut de validation pour les propriétaires"
    )

    id_card = models.FileField(
        upload_to='id_cards/',
        blank=True,
        null=True,
        help_text="Copie de la carte d'identité pour validation propriétaire"
    )

    is_verified_owner = models.BooleanField(
        default=False,
        help_text="Indique si le propriétaire est validé et actif"
    )

    def save(self, *args, **kwargs):
        # Automatically handle owner status default
        if self.role == 'owner' and self.owner_status == 'approved' and not self.is_verified_owner:
            self.owner_status = 'pending'
        elif self.role != 'owner':
            self.owner_status = 'approved'
            self.is_verified_owner = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
