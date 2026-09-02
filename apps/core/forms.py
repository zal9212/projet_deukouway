from django import forms
from django.core.exceptions import ValidationError
import re

# Tailwind v4 standard widget input styling class
TAILWIND_INPUT_CLASS = (
    "w-full rounded-xl border border-gray-300 focus:ring-2 focus:ring-[#8B1E24] "
    "focus:border-[#8B1E24] placeholder:text-gray-400 transition px-4 py-2.5 "
    "text-sm font-medium text-gray-900 bg-white shadow-sm"
)

TAILWIND_CHECKBOX_CLASS = (
    "rounded text-[#8B1E24] focus:ring-[#8B1E24] border-gray-300 transition h-4 w-4"
)

class TailwindFormMixin:
    """
    Mixin pour formulaires Django appliquant automatiquement le Design System
    TailwindCSS v4 et les attributs d'accessibilité (aria-label, autocomplete, etc.).
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_design_system_styles()

    def apply_design_system_styles(self):
        for field_name, field in self.fields.items():
            widget = field.widget

            # Apply Tailwind CSS classes
            if isinstance(widget, (forms.CheckboxInput, forms.RadioSelect)):
                existing_class = widget.attrs.get('class', '')
                widget.attrs['class'] = f"{TAILWIND_CHECKBOX_CLASS} {existing_class}".strip()
            else:
                existing_class = widget.attrs.get('class', '')
                widget.attrs['class'] = f"{TAILWIND_INPUT_CLASS} {existing_class}".strip()

            # Set aria-label if not already present
            if 'aria-label' not in widget.attrs:
                widget.attrs['aria-label'] = str(field.label or field_name.replace('_', ' ').capitalize())

            # Set spellcheck false for emails and passwords
            if isinstance(widget, (forms.EmailInput, forms.PasswordInput)):
                widget.attrs['spellcheck'] = 'false'

def validate_phone_number(value: str) -> str:
    """
    Validateur et normalisateur universel pour les numéros de téléphone.
    Formatte automatiquement tout numéro (ex: 771234567, 77 123 45 67, +22177...)
    """
    if not value or not value.strip():
        return value

    raw = value.strip()
    has_plus = raw.startswith('+')
    digits_only = re.sub(r'\D', '', raw)

    if not digits_only:
        raise ValidationError("Veuillez saisir un numéro de téléphone valide.")

    if len(digits_only) < 7 or len(digits_only) > 15:
        raise ValidationError("Le numéro de téléphone doit contenir entre 7 et 15 chiffres.")

    if has_plus:
        return '+' + digits_only
    elif digits_only.startswith('00'):
        return '+' + digits_only[2:]
    elif digits_only.startswith('221') and len(digits_only) == 12:
        return '+' + digits_only
    elif len(digits_only) == 9:
        return '+221' + digits_only

    return '+' + digits_only

def validate_max_file_size(file_obj, max_size_mb: float = 15.0):
    """Validateur pour vérifier que le fichier ne dépasse pas la taille maximale (ex: 15 Mo)."""
    if file_obj and hasattr(file_obj, 'size'):
        max_bytes = max_size_mb * 1024 * 1024
        if file_obj.size > max_bytes:
            raise ValidationError(f"Le fichier dépasse la taille maximale autorisée de {int(max_size_mb)} Mo.")

def validate_allowed_file_extensions(file_obj, allowed_extensions=('pdf', 'png', 'jpg', 'jpeg')):
    """Validateur pour vérifier l'extension du fichier téléversé."""
    if file_obj and hasattr(file_obj, 'name'):
        ext = file_obj.name.split('.')[-1].lower()
        if ext not in allowed_extensions:
            allowed_str = ", ".join(allowed_extensions).upper()
            raise ValidationError(f"L'extension du fichier '.{ext}' n'est pas autorisée. Formats acceptés: {allowed_str}.")


# Signatures binaires (magic numbers) des formats de fichiers autorisés sur la
# plateforme. Une extension ".jpg" ne prouve rien sur le contenu réel du fichier
# (un exécutable renommé passerait le contrôle par extension) : on vérifie donc
# aussi les premiers octets du fichier avant d'accepter l'upload.
FILE_SIGNATURES = {
    'pdf': [b'%PDF'],
    'jpg': [b'\xff\xd8\xff'],
    'jpeg': [b'\xff\xd8\xff'],
    'png': [b'\x89PNG\r\n\x1a\n'],
    'docx': [b'PK\x03\x04'],
}


def validate_file_content_type(file_obj, allowed_extensions=('pdf', 'png', 'jpg', 'jpeg')):
    """
    Vérifie que le contenu réel du fichier (ses premiers octets) correspond bien
    à l'un des formats autorisés, indépendamment de l'extension déclarée.
    """
    if not file_obj or not hasattr(file_obj, 'read'):
        return

    file_obj.seek(0)
    header = file_obj.read(8)
    file_obj.seek(0)

    valid_signatures = [sig for ext in allowed_extensions for sig in FILE_SIGNATURES.get(ext, [])]
    if not any(header.startswith(sig) for sig in valid_signatures):
        raise ValidationError(
            "Le contenu du fichier ne correspond à aucun format autorisé "
            "(fichier corrompu ou extension trompeuse)."
        )
