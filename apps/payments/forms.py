from typing import Any, Dict, Optional
from django import forms
from django.core.exceptions import ValidationError
from apps.core.forms import TailwindFormMixin, validate_phone_number

PAYMENT_METHOD_CHOICES = (
    ('WAVE', 'Wave Mobile Money'),
    ('ORANGE_MONEY', 'Orange Money'),
    ('CREDIT_CARD', 'Carte bancaire (Visa / Mastercard)'),
)

class PaymentForm(TailwindFormMixin, forms.Form):
    """Formulaire de règlement d'une réservation."""
    method = forms.ChoiceField(
        label="Méthode de paiement",
        choices=PAYMENT_METHOD_CHOICES,
        widget=forms.RadioSelect(),
        error_messages={'required': 'Veuillez sélectionner une méthode de paiement.'}
    )
    phone = forms.CharField(
        label="Numéro de téléphone (Mobile Money)",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '+221 77 000 00 00', 'autocomplete': 'tel'})
    )
    cardholder_name = forms.CharField(
        label="Nom sur la carte",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Moustapha Gaye', 'autocomplete': 'cc-name'})
    )
    card_number = forms.CharField(
        label="Numéro de carte",
        max_length=19,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '4000 1234 5678 9010', 'autocomplete': 'cc-number'})
    )
    card_expiry = forms.CharField(
        label="Date d'expiration (MM/AA)",
        max_length=5,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '12/28', 'autocomplete': 'cc-exp'})
    )
    card_cvc = forms.CharField(
        label="Code CVC / CWW",
        max_length=4,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '123', 'autocomplete': 'cc-csc'})
    )

    def clean_phone(self) -> Optional[str]:
        phone: Optional[str] = self.cleaned_data.get('phone')
        if phone:
            return validate_phone_number(phone)
        return phone

    def clean(self) -> Dict[str, Any]:
        cleaned_data = super().clean()
        method = cleaned_data.get('method')
        phone = cleaned_data.get('phone')
        cardholder = cleaned_data.get('cardholder_name')
        card_num = cleaned_data.get('card_number')

        if method in ['WAVE', 'ORANGE_MONEY']:
            if not phone:
                raise ValidationError({'phone': "Le numéro de téléphone est obligatoire pour le paiement par Mobile Money."})
        elif method == 'CREDIT_CARD':
            if not cardholder:
                raise ValidationError({'cardholder_name': "Le nom du titulaire de la carte est obligatoire."})
            if not card_num:
                raise ValidationError({'card_number': "Le numéro de carte bancaire est obligatoire."})

        return cleaned_data
