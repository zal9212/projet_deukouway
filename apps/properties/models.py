from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel
from .choices import PropertyStatusChoices, PropertyPricingPeriodChoices


class PropertyCategory(BaseModel):
    """
    Catégorie principale d'un logement (ex: Maison, Appartement, Hôtel).
    """
    name = models.CharField(_('Nom'), max_length=100)
    slug = models.SlugField(_('Slug'), unique=True)

    class Meta(BaseModel.Meta):
        verbose_name = _('Catégorie de Propriété')
        verbose_name_plural = _('Catégories de Propriétés')
        db_table = 'properties_category'

    def __str__(self) -> str:
        return str(self.name)


class PropertyType(BaseModel):
    """
    Type spécifique d'un logement lié à une catégorie (ex: Villa, Studio).
    """
    name = models.CharField(_('Nom'), max_length=100)
    slug = models.SlugField(_('Slug'), unique=True)
    category = models.ForeignKey(PropertyCategory, on_delete=models.CASCADE, related_name='types', verbose_name=_('Catégorie'))

    class Meta(BaseModel.Meta):
        verbose_name = _('Type de Propriété')
        verbose_name_plural = _('Types de Propriétés')
        db_table = 'properties_type'

    def __str__(self) -> str:
        return f"{self.category.name} - {self.name}"


class Property(BaseModel):
    """
    Modèle central représentant un bien immobilier mis en location.
    L'owner (propriétaire) n'est jamais le client direct du séjour.
    """
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='properties', verbose_name=_('Propriétaire'))
    property_type = models.ForeignKey(PropertyType, on_delete=models.PROTECT, related_name='properties', verbose_name=_('Type'))
    
    title = models.CharField(_('Titre'), max_length=255)
    description = models.TextField(_('Description'))
    
    # Location
    address = models.CharField(_('Adresse'), max_length=255)
    city = models.CharField(_('Ville'), max_length=100, db_index=True)
    district = models.CharField(_('Quartier'), max_length=100, db_index=True)
    latitude = models.DecimalField(_('Latitude'), max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(_('Longitude'), max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Specs
    price = models.DecimalField(
        _('Prix'),
        max_digits=12,
        decimal_places=2,
        db_index=True,
        validators=[MinValueValidator(0.01)]
    )
    pricing_period = models.CharField(
        _('Type de location'), max_length=10,
        choices=PropertyPricingPeriodChoices.choices, default=PropertyPricingPeriodChoices.NIGHTLY
    )
    surface = models.PositiveIntegerField(_('Surface (m²)'), validators=[MinValueValidator(1)])
    bedrooms = models.PositiveIntegerField(_('Chambres'), validators=[MinValueValidator(0)])
    bathrooms = models.PositiveIntegerField(_('Salles de bain'), validators=[MinValueValidator(0)])
    max_guests = models.PositiveIntegerField(_('Capacité max (personnes)'), validators=[MinValueValidator(1)])
    
    status = models.CharField(
        _('Statut'),
        max_length=20, 
        choices=PropertyStatusChoices.choices, 
        default=PropertyStatusChoices.DRAFT,
        db_index=True
    )

    commission_percentage_override = models.DecimalField(
        _('Pourcentage commission (personnalisé)'),
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0.00), MaxValueValidator(100.00)],
        help_text=_("Pourcentage retenu par DEKOUWAY sur ce logement. Laissez vide pour utiliser le pourcentage par défaut de la plateforme.")
    )

    class Meta(BaseModel.Meta):
        verbose_name = _('Propriété')
        verbose_name_plural = _('Propriétés')
        db_table = 'properties_property'
        constraints = [
            models.CheckConstraint(check=models.Q(price__gt=0), name='check_price_positive'),
            models.CheckConstraint(check=models.Q(surface__gt=0), name='check_surface_positive'),
            models.CheckConstraint(check=models.Q(max_guests__gt=0), name='check_guests_positive')
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.city})"


class PropertyImage(BaseModel):
    """
    Images associées à un logement.
    """
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images', verbose_name=_('Propriété'))
    image = models.ImageField(
        _('Image'),
        upload_to='properties/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])]
    )
    is_cover = models.BooleanField(_('Est l\'image de couverture'), default=False)
    order = models.PositiveIntegerField(_('Ordre d\'affichage'), default=0)

    class Meta(BaseModel.Meta):
        verbose_name = _('Image de Propriété')
        verbose_name_plural = _('Images de Propriétés')
        db_table = 'properties_image'
        ordering = ['order', '-created_at']

    def __str__(self) -> str:
        return f"Image {self.id} - {self.property.title}"


class PropertyAmenity(BaseModel):
    """
    Équipements fournis avec le logement (ex: Wifi, Piscine).
    """
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='amenities', verbose_name=_('Propriété'))
    name = models.CharField(_('Nom de l\'équipement'), max_length=100)
    icon = models.CharField(_('Icône (classe CSS/SVG)'), max_length=50, blank=True)

    class Meta(BaseModel.Meta):
        verbose_name = _('Équipement')
        verbose_name_plural = _('Équipements')
        db_table = 'properties_amenity'

    def __str__(self) -> str:
        return str(self.name)


class PropertyRule(BaseModel):
    """
    Règles spécifiques au logement (ex: Non fumeur, Pas d'animaux).
    """
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='rules', verbose_name=_('Propriété'))
    rule = models.CharField(_('Règle'), max_length=255)

    class Meta(BaseModel.Meta):
        verbose_name = _('Règle de Propriété')
        verbose_name_plural = _('Règles de Propriétés')
        db_table = 'properties_rule'

    def __str__(self) -> str:
        return str(self.rule)


class PropertyAvailability(BaseModel):
    """
    Gestion des disponibilités et des tarifs saisonniers au jour le jour.
    """
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='availabilities', verbose_name=_('Propriété'))
    date = models.DateField(_('Date'))
    is_available = models.BooleanField(_('Est disponible'), default=True)
    price_override = models.DecimalField(_('Prix spécifique'), max_digits=12, decimal_places=2, null=True, blank=True)

    class Meta(BaseModel.Meta):
        verbose_name = _('Disponibilité')
        verbose_name_plural = _('Disponibilités')
        db_table = 'properties_availability'
        constraints = [
            models.UniqueConstraint(fields=['property', 'date'], name='unique_property_date_availability')
        ]

    def __str__(self) -> str:
        return f"{self.property.title} - {self.date} ({'Dispo' if self.is_available else 'Réservé'})"


class PropertyValidation(BaseModel):
    """
    Historique de validation d'un logement par le SuperAdmin.
    """
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='validations', verbose_name=_('Propriété'))
    validator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='validated_properties', verbose_name=_('Validateur'))
    is_approved = models.BooleanField(_('Est approuvé'), default=False)
    comments = models.TextField(_('Commentaires'), blank=True)

    class Meta(BaseModel.Meta):
        verbose_name = _('Validation de Propriété')
        verbose_name_plural = _('Validations de Propriétés')
        db_table = 'properties_validation'

    def __str__(self) -> str:
        return f"Validation {self.id} - {self.property.title}"


class PropertyStatusHistory(BaseModel):
    """
    Traçabilité des changements d'états d'une propriété.
    """
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='status_history', verbose_name=_('Propriété'))
    old_status = models.CharField(_('Ancien Statut'), max_length=20, choices=PropertyStatusChoices.choices)
    new_status = models.CharField(_('Nouveau Statut'), max_length=20, choices=PropertyStatusChoices.choices)
    reason = models.TextField(_('Raison du changement'), blank=True)

    class Meta(BaseModel.Meta):
        verbose_name = _('Historique de Statut Propriété')
        verbose_name_plural = _('Historiques de Statuts Propriétés')
        db_table = 'properties_status_history'

    def __str__(self) -> str:
        return f"{self.property.title}: {self.old_status} -> {self.new_status}"


class PropertyFavorite(BaseModel):
    """
    Système de favoris pour les clients.
    """
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='favorited_by', verbose_name=_('Propriété'))
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorite_properties', verbose_name=_('Utilisateur'))

    class Meta(BaseModel.Meta):
        verbose_name = _('Favori')
        verbose_name_plural = _('Favoris')
        db_table = 'properties_favorite'
        constraints = [
            models.UniqueConstraint(fields=['property', 'user'], name='unique_property_user_favorite')
        ]

    def __str__(self) -> str:
        return f"{self.user.email} - {self.property.title}"


class PropertyReview(BaseModel):
    """
    Avis et notes laissés par les clients sur les logements après séjour.
    """
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='reviews', verbose_name=_('Propriété'))
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='property_reviews', verbose_name=_('Auteur'))
    reservation = models.ForeignKey('reservations.Reservation', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews', verbose_name=_('Réservation'))
    rating = models.PositiveSmallIntegerField(_('Note (1 à 5)'), validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(_('Commentaire'), blank=True)

    class Meta(BaseModel.Meta):
        verbose_name = _('Avis Logement')
        verbose_name_plural = _('Avis Logements')
        db_table = 'properties_review'

    def __str__(self) -> str:
        return f"{self.rating}/5 par {self.user.email} sur {self.property.title}"

