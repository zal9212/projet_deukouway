from typing import Any, Dict, Optional
from django import forms
from django.core.exceptions import ValidationError
from apps.core.forms import TailwindFormMixin
from apps.properties.choices import PropertyPricingPeriodChoices

SORT_CHOICES = (
    ('', 'Trier par...'),
    ('newest', 'Plus récents'),
    ('price_asc', 'Prix croissant'),
    ('price_desc', 'Prix décroissant'),
)

PROPERTY_TYPE_CHOICES = (
    ('', 'Tous les types'),
    ('villa', 'Villa'),
    ('appartement', 'Appartement'),
    ('studio', 'Studio'),
    ('maison', 'Maison d\'hôte'),
)


class SearchForm(TailwindFormMixin, forms.Form):
    """Formulaire de recherche et filtrage avancé des logements."""
    q = forms.CharField(
        label="Recherche textuelle",
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Ex: Villa Almadies avec piscine...'})
    )
    city = forms.CharField(
        label="Ville",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Dakar, Saly, Somone...', 'autocomplete': 'address-level2'})
    )
    district = forms.CharField(
        label="Quartier",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Almadies, Ngor, Fann...'})
    )
    min_price = forms.DecimalField(
        label="Prix min (FCFA)",
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={'placeholder': '20000', 'min': '0'})
    )
    max_price = forms.DecimalField(
        label="Prix max (FCFA)",
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={'placeholder': '200000', 'min': '0'})
    )
    bedrooms = forms.IntegerField(
        label="Chambres min",
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={'placeholder': '1', 'min': '0'})
    )
    bathrooms = forms.IntegerField(
        label="Salles de bain min",
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={'placeholder': '1', 'min': '0'})
    )
    surface = forms.IntegerField(
        label="Surface min (m²)",
        min_value=1,
        required=False,
        widget=forms.NumberInput(attrs={'placeholder': '50', 'min': '1'})
    )
    property_type = forms.ChoiceField(
        label="Type de bien",
        choices=PROPERTY_TYPE_CHOICES,
        required=False,
        widget=forms.Select()
    )
    equipments = forms.CharField(
        label="Équipements (séparés par des virgules)",
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Piscine, Climatisation, Wifi...'})
    )
    sort_by = forms.ChoiceField(
        label="Tri",
        choices=SORT_CHOICES,
        required=False,
        widget=forms.Select()
    )

    def clean_surface(self) -> Optional[int]:
        surface: Optional[int] = self.cleaned_data.get('surface')
        if surface is not None and surface <= 0:
            raise ValidationError("La surface doit être strictly positive.")
        return surface

    def clean(self) -> Dict[str, Any]:
        cleaned_data = super().clean()
        min_p = cleaned_data.get('min_price')
        max_p = cleaned_data.get('max_price')
        if min_p is not None and max_p is not None and min_p > max_p:
            raise ValidationError("Le prix minimum ne peut pas être supérieur au prix maximum.")
        return cleaned_data


class PropertyForm(TailwindFormMixin, forms.Form):
    """Formulaire de création et édition d'un logement par le propriétaire."""
    title = forms.CharField(
        label="Nom du logement",
        max_length=255,
        widget=forms.TextInput(attrs={'placeholder': 'Splendide Villa Keur Thiossane avec Piscine', 'required': 'required'}),
        error_messages={'required': 'Veuillez saisir le nom de votre logement.'}
    )
    description = forms.CharField(
        label="Description détaillée",
        widget=forms.Textarea(attrs={'placeholder': 'Décrivez les caractéristiques du logement, sa localisation...', 'rows': 4, 'required': 'required'}),
        error_messages={'required': 'Veuillez saisir une description.'}
    )
    price = forms.DecimalField(
        label="Prix (FCFA)",
        max_digits=12,
        decimal_places=2,
        min_value=0.01,
        widget=forms.NumberInput(attrs={'placeholder': '120000', 'min': '0.01', 'step': '0.01', 'required': 'required'}),
        error_messages={'required': 'Veuillez indiquer le prix.'}
    )
    pricing_period = forms.ChoiceField(
        label="Type de location",
        choices=PropertyPricingPeriodChoices.choices,
        required=False,
        widget=forms.RadioSelect()
    )
    address = forms.CharField(
        label="Adresse exacte",
        max_length=255,
        widget=forms.TextInput(attrs={'placeholder': 'Rue 10 x Rue 12 Almadies', 'autocomplete': 'street-address', 'required': 'required'}),
        error_messages={'required': 'Veuillez préciser l\'adresse.'}
    )
    city = forms.CharField(
        label="Ville",
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Dakar', 'autocomplete': 'address-level2', 'required': 'required'}),
        error_messages={'required': 'Veuillez indiquer la ville.'}
    )
    district = forms.CharField(
        label="Quartier",
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Almadies', 'required': 'required'}),
        error_messages={'required': 'Veuillez indiquer le quartier.'}
    )
    latitude = forms.DecimalField(
        label="Latitude (optionnelle)",
        max_digits=9,
        decimal_places=6,
        required=False,
        widget=forms.NumberInput(attrs={'placeholder': '14.745400', 'step': 'any'})
    )
    longitude = forms.DecimalField(
        label="Longitude (optionnelle)",
        max_digits=9,
        decimal_places=6,
        required=False,
        widget=forms.NumberInput(attrs={'placeholder': '-17.514300', 'step': 'any'})
    )
    surface = forms.IntegerField(
        label="Surface (m²)",
        min_value=1,
        widget=forms.NumberInput(attrs={'placeholder': '200', 'min': '1', 'required': 'required'}),
        error_messages={'required': 'Veuillez préciser la surface.'}
    )
    bedrooms = forms.IntegerField(
        label="Nombre de chambres",
        min_value=0,
        widget=forms.NumberInput(attrs={'placeholder': '3', 'min': '0', 'required': 'required'})
    )
    bathrooms = forms.IntegerField(
        label="Nombre de salles de bain",
        min_value=0,
        widget=forms.NumberInput(attrs={'placeholder': '2', 'min': '0', 'required': 'required'})
    )
    max_guests = forms.IntegerField(
        label="Capacité d'accueil max (personnes)",
        min_value=1,
        widget=forms.NumberInput(attrs={'placeholder': '6', 'min': '1', 'required': 'required'})
    )
    property_type_id = forms.CharField(
        label="Type de bien (ID)",
        widget=forms.TextInput(attrs={'required': 'required'})
    )

    def clean_price(self) -> Optional[Any]:
        price = self.cleaned_data.get('price')
        if price is not None and price <= 0:
            raise ValidationError("Le prix doit être strictement positif.")
        return price

    def clean_surface(self) -> Optional[int]:
        surface: Optional[int] = self.cleaned_data.get('surface')
        if surface is not None and surface <= 0:
            raise ValidationError("La surface doit être strictement supérieure à 0 m².")
        return surface

    def clean(self) -> Dict[str, Any]:
        cleaned_data = super().clean()
        if not cleaned_data.get('pricing_period'):
            cleaned_data['pricing_period'] = PropertyPricingPeriodChoices.NIGHTLY
        lat = cleaned_data.get('latitude')
        lng = cleaned_data.get('longitude')
        if lat is not None and (lat < -90 or lat > 90):
            raise ValidationError({'latitude': "La latitude doit être comprise entre -90 et 90 degrés."})
        if lng is not None and (lng < -180 or lng > 180):
            raise ValidationError({'longitude': "La longitude doit être comprise entre -180 et 180 degrés."})
        return cleaned_data
