from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model

User = get_user_model()

class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label="Prénom")
    last_name = forms.CharField(max_length=30, required=True, label="Nom")
    email = forms.EmailField(required=True, label="Adresse Email")
    phone = forms.CharField(max_length=20, required=True, label="Téléphone (ex: +221770000000)")
    
    role = forms.ChoiceField(
        choices=(
            ('client', 'Client (Je cherche un logement)'),
            ('owner', 'Propriétaire (Je loue des logements)')
        ),
        widget=forms.RadioSelect,
        initial='client',
        label="Type de compte"
    )
    
    id_card = forms.FileField(
        required=False,
        label="Pièce d'identité (Requis uniquement pour les Propriétaires)",
        help_text="Format PDF ou Image"
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone', 'role', 'id_card')

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get("role")
        id_card = cleaned_data.get("id_card")

        if role == 'owner' and not id_card:
            self.add_error('id_card', "La pièce d'identité est obligatoire pour s'inscrire en tant que propriétaire.")
        return cleaned_data


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone', 'avatar')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-xl dark:bg-slate-800 dark:border-slate-700'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-xl dark:bg-slate-800 dark:border-slate-700'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-4 py-2 border rounded-xl dark:bg-slate-800 dark:border-slate-700'}),
            'phone': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-xl dark:bg-slate-800 dark:border-slate-700'}),
            'avatar': forms.FileInput(attrs={'class': 'hidden', 'id': 'avatar-input'}),
        }
