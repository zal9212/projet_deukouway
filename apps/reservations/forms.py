from typing import Any, Dict, Optional
from datetime import date
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.core.forms import TailwindFormMixin

class ReservationRequestForm(TailwindFormMixin, forms.Form):
    """Formulaire de demande de réservation d'un logement."""
    check_in = forms.DateField(
        label="Date d'arrivée",
        widget=forms.DateInput(attrs={
            'type': 'date',
            'required': 'required',
            'min': timezone.now().date().isoformat()
        }),
        error_messages={'required': 'Veuillez sélectionner votre date d\'arrivée.'}
    )
    check_out = forms.DateField(
        label="Date de départ",
        widget=forms.DateInput(attrs={
            'type': 'date',
            'required': 'required',
            'min': timezone.now().date().isoformat()
        }),
        error_messages={'required': 'Veuillez sélectionner votre date de départ.'}
    )
    guests = forms.IntegerField(
        label="Nombre de personnes",
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={'min': '1', 'max': '50', 'required': 'required'}),
        error_messages={'required': 'Veuillez indiquer le nombre de personnes.'}
    )
    special_requests = forms.CharField(
        label="Demandes spéciales / Message au propriétaire",
        required=False,
        widget=forms.Textarea(attrs={
            'placeholder': 'Précisez l\'heure d\'arrivée souhaitée, vos besoins particuliers...',
            'rows': 3
        })
    )

    def clean_guests(self) -> Optional[int]:
        guests: Optional[int] = self.cleaned_data.get('guests')
        if guests is not None and guests <= 0:
            raise ValidationError("Le nombre de personnes doit être supérieur à zéro.")
        return guests

    def clean(self) -> Dict[str, Any]:
        cleaned_data = super().clean()
        check_in: Optional[date] = cleaned_data.get('check_in')
        check_out: Optional[date] = cleaned_data.get('check_out')
        today = timezone.now().date()

        if check_in and check_in < today:
            raise ValidationError({'check_in': "La date d'arrivée ne peut pas être dans le passé."})

        if check_in and check_out:
            if check_out <= check_in:
                raise ValidationError({'check_out': "La date de départ doit être strictement supérieure à la date d'arrivée."})

        return cleaned_data
