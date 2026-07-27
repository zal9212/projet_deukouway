from typing import Any, Dict, Optional
from django import forms
from django.core.exceptions import ValidationError
from apps.core.forms import (
    TailwindFormMixin, validate_phone_number,
    validate_max_file_size, validate_allowed_file_extensions, validate_file_content_type
)

class LoginForm(TailwindFormMixin, forms.Form):
    """Formulaire de connexion d'un utilisateur sur la plateforme DEKOUWAY."""
    email = forms.EmailField(
        label="Adresse e-mail",
        widget=forms.EmailInput(attrs={
            'autocomplete': 'email',
            'placeholder': 'exemple@dekouway.sn',
            'required': 'required',
            'spellcheck': 'false',
        }),
        error_messages={'required': 'Veuillez renseigner votre adresse e-mail.'}
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'current-password',
            'placeholder': '••••••••',
            'required': 'required',
            'spellcheck': 'false',
        }),
        error_messages={'required': 'Veuillez renseigner votre mot de passe.'}
    )


class ClientRegisterForm(TailwindFormMixin, forms.Form):
    """Formulaire d'inscription pour un client / locataire."""
    first_name = forms.CharField(
        label="Prénom",
        max_length=150,
        widget=forms.TextInput(attrs={
            'placeholder': 'Moustapha',
            'autocomplete': 'given-name',
            'required': 'required'
        }),
        error_messages={'required': 'Veuillez renseigner votre prénom.'}
    )
    last_name = forms.CharField(
        label="Nom",
        max_length=150,
        widget=forms.TextInput(attrs={
            'placeholder': 'Gaye',
            'autocomplete': 'family-name',
            'required': 'required'
        }),
        error_messages={'required': 'Veuillez renseigner votre nom.'}
    )
    email = forms.EmailField(
        label="Adresse e-mail",
        widget=forms.EmailInput(attrs={
            'autocomplete': 'email',
            'placeholder': 'client@dekouway.sn',
            'required': 'required',
            'spellcheck': 'false'
        }),
        error_messages={'required': 'Veuillez renseigner votre adresse e-mail.'}
    )
    phone = forms.CharField(
        label="Numéro de téléphone",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': '+221 77 000 00 00',
            'autocomplete': 'tel'
        })
    )
    password1 = forms.CharField(
        label="Mot de passe",
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'placeholder': '••••••••',
            'autocomplete': 'new-password',
            'required': 'required',
            'spellcheck': 'false'
        }),
        error_messages={'required': 'Veuillez renseigner un mot de passe.'}
    )
    password2 = forms.CharField(
        label="Confirmation du mot de passe",
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'placeholder': '••••••••',
            'autocomplete': 'new-password',
            'required': 'required',
            'spellcheck': 'false'
        }),
        error_messages={'required': 'Veuillez confirmer votre mot de passe.'}
    )
    accept_terms = forms.BooleanField(
        label="J'accepte les conditions générales d'utilisation",
        required=True,
        error_messages={'required': 'Vous devez accepter les conditions générales.'}
    )

    def clean_phone(self) -> Optional[str]:
        phone: Optional[str] = self.cleaned_data.get('phone')
        if phone:
            return validate_phone_number(phone)
        return phone

    def clean(self) -> Dict[str, Any]:
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise ValidationError({'password2': "Les mots de passe ne correspondent pas."})
        return cleaned_data


# Alias ClientRegistrationForm pour rétrocompatibilité
ClientRegistrationForm = ClientRegisterForm


class OwnerRegisterForm(TailwindFormMixin, forms.Form):
    """Formulaire d'inscription pour un propriétaire bailleur."""
    first_name = forms.CharField(
        label="Prénom",
        max_length=150,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ibrahima',
            'autocomplete': 'given-name',
            'required': 'required'
        }),
        error_messages={'required': 'Veuillez renseigner votre prénom.'}
    )
    last_name = forms.CharField(
        label="Nom",
        max_length=150,
        widget=forms.TextInput(attrs={
            'placeholder': 'Diop',
            'autocomplete': 'family-name',
            'required': 'required'
        }),
        error_messages={'required': 'Veuillez renseigner votre nom.'}
    )
    email = forms.EmailField(
        label="Adresse e-mail",
        widget=forms.EmailInput(attrs={
            'autocomplete': 'email',
            'placeholder': 'proprietaire@dekouway.sn',
            'required': 'required',
            'spellcheck': 'false'
        }),
        error_messages={'required': 'Veuillez renseigner votre adresse e-mail.'}
    )
    phone = forms.CharField(
        label="Numéro de téléphone",
        max_length=20,
        widget=forms.TextInput(attrs={
            'placeholder': '+221 77 111 22 33',
            'autocomplete': 'tel',
            'required': 'required'
        }),
        error_messages={'required': 'Veuillez renseigner votre numéro de téléphone.'}
    )
    company_name = forms.CharField(
        label="Nom de l'entreprise (optionnel)",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Teranga Immobilier SARL',
            'autocomplete': 'organization'
        })
    )
    ninea = forms.CharField(
        label="Numéro NINEA (optionnel)",
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '001234567 2G3'})
    )
    address = forms.CharField(
        label="Adresse postale",
        max_length=255,
        widget=forms.TextInput(attrs={
            'placeholder': 'Avenue Cheikh Anta Diop',
            'autocomplete': 'street-address',
            'required': 'required'
        }),
        error_messages={'required': 'Veuillez renseigner votre adresse.'}
    )
    city = forms.CharField(
        label="Ville",
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Dakar',
            'autocomplete': 'address-level2',
            'required': 'required'
        }),
        error_messages={'required': 'Veuillez renseigner votre ville.'}
    )
    document_type = forms.ChoiceField(
        label="Type de pièce d'identité",
        choices=[
            ('CNI', "Carte Nationale d'Identité"),
            ('PASSEPORT', "Passeport"),
            ('TITRE_SEJOUR', "Titre de séjour"),
        ],
        widget=forms.Select(attrs={'required': 'required'}),
        error_messages={'required': 'Veuillez indiquer le type de votre pièce d\'identité.'}
    )
    document_number = forms.CharField(
        label="Numéro du document",
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': '1 2345 6789 0123',
            'required': 'required'
        }),
        error_messages={'required': 'Veuillez renseigner le numéro de votre pièce d\'identité.'}
    )
    identity_file = forms.FileField(
        label="Photo de la pièce d'identité (PDF, PNG, JPG - max 5 Mo)",
        required=True,
        widget=forms.FileInput(attrs={'accept': '.pdf,.png,.jpg,.jpeg', 'required': 'required'}),
        error_messages={'required': "Veuillez téléverser une photo lisible de votre pièce d'identité."}
    )
    selfie_with_id_file = forms.ImageField(
        label="Selfie tenant la pièce d'identité (PNG, JPG - max 5 Mo)",
        required=True,
        widget=forms.FileInput(attrs={'accept': '.png,.jpg,.jpeg', 'required': 'required'}),
        error_messages={'required': "Veuillez téléverser un selfie de vous tenant votre pièce d'identité, visage et document bien visibles."}
    )
    password1 = forms.CharField(
        label="Mot de passe",
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'placeholder': '••••••••',
            'autocomplete': 'new-password',
            'required': 'required',
            'spellcheck': 'false'
        }),
        error_messages={'required': 'Veuillez renseigner un mot de passe.'}
    )
    password2 = forms.CharField(
        label="Confirmation du mot de passe",
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'placeholder': '••••••••',
            'autocomplete': 'new-password',
            'required': 'required',
            'spellcheck': 'false'
        }),
        error_messages={'required': 'Veuillez confirmer votre mot de passe.'}
    )
    accept_terms = forms.BooleanField(
        label="J'accepte les conditions générales d'utilisation",
        required=True,
        error_messages={'required': 'Vous devez accepter les conditions générales.'}
    )

    def clean_phone(self) -> Optional[str]:
        phone: Optional[str] = self.cleaned_data.get('phone')
        if phone:
            return validate_phone_number(phone)
        return phone

    def clean_identity_file(self) -> Any:
        file_obj = self.cleaned_data.get('identity_file')
        if file_obj:
            validate_allowed_file_extensions(file_obj, ('pdf', 'png', 'jpg', 'jpeg'))
            validate_file_content_type(file_obj, ('pdf', 'png', 'jpg', 'jpeg'))
            validate_max_file_size(file_obj, max_size_mb=5.0)
        return file_obj

    def clean_selfie_with_id_file(self) -> Any:
        file_obj = self.cleaned_data.get('selfie_with_id_file')
        if file_obj:
            validate_allowed_file_extensions(file_obj, ('png', 'jpg', 'jpeg'))
            validate_max_file_size(file_obj, max_size_mb=5.0)
        return file_obj

    def clean(self) -> Dict[str, Any]:
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise ValidationError({'password2': "Les mots de passe ne correspondent pas."})
        return cleaned_data


# Alias OwnerRegistrationForm pour rétrocompatibilité
OwnerRegistrationForm = OwnerRegisterForm


class ProfileForm(TailwindFormMixin, forms.Form):
    """Formulaire de mise à jour du profil utilisateur."""
    first_name = forms.CharField(
        label="Prénom",
        max_length=150,
        widget=forms.TextInput(attrs={
            'placeholder': 'Prénom',
            'autocomplete': 'given-name',
            'required': 'required'
        })
    )
    last_name = forms.CharField(
        label="Nom",
        max_length=150,
        widget=forms.TextInput(attrs={
            'placeholder': 'Nom',
            'autocomplete': 'family-name',
            'required': 'required'
        })
    )
    phone = forms.CharField(
        label="Téléphone",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': '+221 77 000 00 00',
            'autocomplete': 'tel'
        })
    )
    address = forms.CharField(
        label="Adresse",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Rue des Almadies',
            'autocomplete': 'street-address'
        })
    )
    city = forms.CharField(
        label="Ville",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Dakar',
            'autocomplete': 'address-level2'
        })
    )
    country = forms.CharField(
        label="Pays",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Sénégal',
            'autocomplete': 'country-name'
        })
    )
    bio = forms.CharField(
        label="Biographie / Présentation",
        required=False,
        widget=forms.Textarea(attrs={'placeholder': 'Présentez-vous brièvement...', 'rows': 3})
    )
    avatar = forms.ImageField(
        label="Photo de profil",
        required=False,
        widget=forms.FileInput(attrs={'accept': 'image/png,image/jpeg,image/jpg,image/webp'})
    )

    def clean_phone(self) -> Optional[str]:
        phone: Optional[str] = self.cleaned_data.get('phone')
        if phone:
            return validate_phone_number(phone)
        return phone

    def clean_avatar(self) -> Any:
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            validate_allowed_file_extensions(avatar, ('png', 'jpg', 'jpeg', 'webp'))
            validate_max_file_size(avatar, max_size_mb=5.0)
        return avatar


class SecurityForm(TailwindFormMixin, forms.Form):
    """Formulaire de changement de mot de passe."""
    old_password = forms.CharField(
        label="Ancien mot de passe",
        widget=forms.PasswordInput(attrs={
            'placeholder': '••••••••',
            'autocomplete': 'current-password',
            'required': 'required',
            'spellcheck': 'false'
        }),
        error_messages={'required': 'Veuillez saisir votre ancien mot de passe.'}
    )
    new_password = forms.CharField(
        label="Nouveau mot de passe",
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'placeholder': '••••••••',
            'autocomplete': 'new-password',
            'required': 'required',
            'spellcheck': 'false'
        }),
        error_messages={'required': 'Veuillez saisir le nouveau mot de passe.'}
    )
    password_confirm = forms.CharField(
        label="Confirmation du nouveau mot de passe",
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'placeholder': '••••••••',
            'autocomplete': 'new-password',
            'required': 'required',
            'spellcheck': 'false'
        }),
        error_messages={'required': 'Veuillez confirmer le nouveau mot de passe.'}
    )

    def clean(self) -> Dict[str, Any]:
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password')
        p2 = cleaned_data.get('password_confirm')
        if p1 and p2 and p1 != p2:
            raise ValidationError({'password_confirm': "Les mots de passe ne correspondent pas."})
        return cleaned_data
