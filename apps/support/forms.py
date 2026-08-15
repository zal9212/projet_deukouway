from django import forms
from django.core.exceptions import ValidationError
from apps.core.forms import TailwindFormMixin

PRIORITY_CHOICES = (
    ('LOW', 'Basse'),
    ('MEDIUM', 'Moyenne'),
    ('HIGH', 'Haute'),
    ('URGENT', 'Urgente'),
)

class SupportTicketForm(TailwindFormMixin, forms.Form):
    """Formulaire de création d'un ticket de support client/propriétaire."""
    subject = forms.CharField(
        label="Sujet de la demande",
        max_length=255,
        min_length=5,
        widget=forms.TextInput(attrs={'placeholder': 'Ex: Problème d\'accès au logement', 'required': 'required'}),
        error_messages={
            'required': 'Veuillez renseigner le sujet de votre demande.',
            'min_length': 'Le sujet doit comporter au moins 5 caractères.'
        }
    )
    category_id = forms.CharField(
        label="Catégorie de la demande",
        widget=forms.TextInput(attrs={'required': 'required'}),
        error_messages={'required': 'Veuillez sélectionner une catégorie.'}
    )
    priority = forms.ChoiceField(
        label="Priorité",
        choices=PRIORITY_CHOICES,
        initial='MEDIUM',
        widget=forms.Select()
    )
    description = forms.CharField(
        label="Description détaillée du problème",
        min_length=15,
        widget=forms.Textarea(attrs={'placeholder': 'Expliquez en détail votre situation...', 'rows': 5, 'required': 'required'}),
        error_messages={
            'required': 'Veuillez décrire votre problème.',
            'min_length': 'La description doit comporter au moins 15 caractères.'
        }
    )

    def clean_subject(self) -> str:
        subject: str = self.cleaned_data.get('subject', '').strip()
        if len(subject) < 5:
            raise ValidationError("Le sujet doit comporter au moins 5 caractères.")
        return subject

    def clean_description(self) -> str:
        description: str = self.cleaned_data.get('description', '').strip()
        if len(description) < 15:
            raise ValidationError("La description détaillée doit comporter au moins 15 caractères.")
        return description
