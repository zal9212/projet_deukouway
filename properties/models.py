from django.db import models
from django.conf import settings

class Amenity(models.Model):
    """
    Features/Equipments available in a property (e.g. Wi-Fi, Pool, AC).
    """
    name = models.CharField(max_length=50, unique=True)
    icon = models.CharField(
        max_length=30, 
        default='check', 
        help_text="Name of the Lucide icon to display (e.g., 'wifi', 'wind', 'tv')"
    )

    class Meta:
        verbose_name = "Équipement"
        verbose_name_plural = "Équipements"

    def __str__(self):
        return self.name


class Property(models.Model):
    """
    Real estate listings posted by owners and moderated by administrators.
    """
    TYPE_CHOICES = (
        ('apartment', 'Appartement'),
        ('villa', 'Villa'),
        ('studio', 'Studio'),
        ('room', 'Chambre d\'hôte'),
    )

    STATUS_CHOICES = (
        ('pending', 'En attente de validation'),
        ('approved', 'Publié'),
        ('rejected', 'Rejeté'),
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='properties',
        limit_choices_to={'role': 'owner'}
    )
    title = models.CharField(max_length=150, verbose_name="Titre de l'annonce")
    description = models.TextField(verbose_name="Description détaillée")
    
    property_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='apartment',
        verbose_name="Type de logement"
    )
    
    price_per_night = models.DecimalField(
        max_length=12,
        max_digits=12,
        decimal_places=0,
        verbose_name="Prix par nuit (FCFA)"
    )
    
    address = models.CharField(max_length=255, verbose_name="Adresse")
    city = models.CharField(max_length=100, verbose_name="Ville")
    neighborhood = models.CharField(max_length=100, verbose_name="Quartier")
    
    # Location coordinates for interactive Leaflet maps
    latitude = models.FloatField(default=14.7167, verbose_name="Latitude") # Default near Dakar
    longitude = models.FloatField(default=-17.4677, verbose_name="Longitude")
    
    capacity = models.PositiveIntegerField(default=2, verbose_name="Capacité (personnes)")
    bedrooms = models.PositiveIntegerField(default=1, verbose_name="Nombre de chambres")
    bathrooms = models.PositiveIntegerField(default=1, verbose_name="Nombre de salles de bain")
    
    amenities = models.ManyToManyField(
        Amenity,
        blank=True,
        related_name='properties',
        verbose_name="Équipements"
    )
    
    is_available = models.BooleanField(default=True, verbose_name="Disponible à la location")
    
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Statut de validation"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Logement"
        verbose_name_plural = "Logements"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.city} ({self.get_property_type_display()})"


class PropertyImage(models.Model):
    """
    Media gallery files uploaded for a specific property listing.
    """
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.FileField(upload_to='properties/')
    is_main = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Image du logement"
        verbose_name_plural = "Images du logement"

    def __str__(self):
        return f"Image for {self.property.title}"
