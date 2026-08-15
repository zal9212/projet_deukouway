from typing import Any
from django import forms
from django.core.exceptions import ValidationError
from apps.core.forms import (
    TailwindFormMixin, validate_max_file_size, validate_allowed_file_extensions
)

DOCUMENT_TYPE_CHOICES = (
    ('CNI', 'Carte Nationale d\'Identité (CNI)'),
    ('PASSPORT', 'Passeport international'),
    ('PROPERTY_TITLE', 'Titre de propriété / Bail'),
    ('RIB', 'Relevé d\'Identité Bancaire (RIB)'),
    ('OTHER', 'Autre justificatif'),
)

class DocumentUploadForm(TailwindFormMixin, forms.Form):
    """Formulaire de téléversement de documents (KYC, Titres, Justificatifs)."""
    document_type = forms.ChoiceField(
        label="Type de document",
        choices=DOCUMENT_TYPE_CHOICES,
        widget=forms.Select(attrs={'required': 'required'}),
        error_messages={'required': 'Veuillez sélectionner le type de document.'}
    )
    document_number = forms.CharField(
        label="Numéro du document (optionnel)",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Ex: 1754199001234'})
    )
    file = forms.FileField(
        label="Fichier (PDF, PNG, JPG, JPEG - 5 Mo max)",
        required=True,
        widget=forms.FileInput(attrs={'accept': '.pdf,.png,.jpg,.jpeg', 'required': 'required'}),
        error_messages={'required': 'Veuillez sélectionner un fichier à téléverser.'}
    )
    description = forms.CharField(
        label="Description / Remarques (optionnel)",
        required=False,
        widget=forms.Textarea(attrs={'placeholder': 'Précisions sur le document transmis...', 'rows': 2})
    )

    def clean_file(self) -> Any:
        file_obj = self.cleaned_data.get('file')
        if not file_obj:
            raise ValidationError("Veuillez sélectionner un fichier.")
        validate_allowed_file_extensions(file_obj, ('pdf', 'png', 'jpg', 'jpeg'))
        validate_max_file_size(file_obj, max_size_mb=5.0)
        return file_obj
