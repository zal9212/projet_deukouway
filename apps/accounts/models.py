from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator, FileExtensionValidator
from apps.core.models import BaseModel
from apps.core.storage import private_storage
from .managers import UserManager


class User(AbstractUser, BaseModel):
    """
    Modèle utilisateur personnalisé centralisant l'authentification SaaS.
    """
    username = None  # Suppression stricte du username
    email = models.EmailField(_('Adresse email'), unique=True, db_index=True)
    
    # Rôles métiers
    is_client = models.BooleanField(_('Est un client'), default=True)
    is_owner = models.BooleanField(_('Est un propriétaire'), default=False)
    is_superadmin = models.BooleanField(_('Est SuperAdmin'), default=False)

    # Vérification KYC propriétaire : distincte de `is_active` (qui gère la
    # capacité de connexion / le blocage par un admin). Un propriétaire peut
    # se connecter dès son inscription mais ne peut publier de logement tant
    # qu'un SuperAdmin n'a pas validé sa pièce d'identité.
    is_verified = models.BooleanField(_('Propriétaire vérifié (KYC)'), default=False)

    email_verified = models.BooleanField(_('Email vérifié'), default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta(BaseModel.Meta):
        verbose_name = _('Utilisateur')
        verbose_name_plural = _('Utilisateurs')
        db_table = 'accounts_user'

    def __str__(self) -> str:
        return str(self.email)


class UserProfile(BaseModel):
    """
    Profil étendu contenant les informations personnelles d'un utilisateur.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name=_('Utilisateur'))
    first_name = models.CharField(_('Prénom'), max_length=150)
    last_name = models.CharField(_('Nom'), max_length=150)
    
    # Validateur strict pour téléphone (ex: +33612345678 ou 0612345678)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$', 
        message=_("Le numéro de téléphone doit être au format: '+999999999'. Jusqu'à 15 chiffres.")
    )
    phone = models.CharField(_('Téléphone'), validators=[phone_regex], max_length=20, blank=True, null=True, db_index=True)
    
    avatar = models.ImageField(
        _('Avatar'), 
        upload_to='avatars/', 
        blank=True, 
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])]
    )
    birth_date = models.DateField(_('Date de naissance'), blank=True, null=True)
    
    class Meta(BaseModel.Meta):
        verbose_name = _('Profil Utilisateur')
        verbose_name_plural = _('Profils Utilisateurs')
        db_table = 'accounts_user_profile'

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Address(BaseModel):
    """
    Gestion des adresses postales pour la facturation et l'identification.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses', verbose_name=_('Utilisateur'))
    street = models.CharField(_('Rue'), max_length=255)
    city = models.CharField(_('Ville'), max_length=100, db_index=True)
    postal_code = models.CharField(_('Code postal'), max_length=20)
    country = models.CharField(_('Pays'), max_length=100)
    is_default = models.BooleanField(_('Est par défaut'), default=False)

    class Meta(BaseModel.Meta):
        verbose_name = _('Adresse')
        verbose_name_plural = _('Adresses')
        db_table = 'accounts_address'

    def __str__(self) -> str:
        return f"{self.street}, {self.postal_code} {self.city} ({self.country})"


class IdentityDocument(BaseModel):
    """
    Stockage sécurisé des pièces d'identité pour vérification (KYC).
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='identity_documents', verbose_name=_('Utilisateur'))
    document_type = models.CharField(_('Type de document'), max_length=50) # ex: CNI, PASSPORT
    document_number = models.CharField(_('Numéro de document'), max_length=100)
    file = models.FileField(
        _('Fichier (pièce d\'identité, recto)'),
        upload_to='identity_documents/',
        storage=private_storage,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )
    file_back = models.FileField(
        _('Fichier (pièce d\'identité, verso)'),
        upload_to='identity_documents/',
        storage=private_storage,
        null=True, blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])],
        help_text=_("Obligatoire pour une carte nationale d'identité (recto/verso) ; sans objet pour un passeport.")
    )
    selfie_file = models.ImageField(
        _('Selfie avec la pièce d\'identité'),
        upload_to='identity_documents/selfies/',
        storage=private_storage,
        null=True, blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])],
        help_text=_("Photo du titulaire tenant sa pièce d'identité, pour vérification anti-fraude.")
    )
    is_verified = models.BooleanField(_('Est vérifié'), default=False)
    verified_at = models.DateTimeField(_('Date de vérification'), null=True, blank=True)
    
    class Meta(BaseModel.Meta):
        verbose_name = _('Pièce d\'identité')
        verbose_name_plural = _('Pièces d\'identité')
        db_table = 'accounts_identity_document'

    def __str__(self) -> str:
        return f"{self.document_type} - {self.user.email}"


class UserSession(BaseModel):
    """
    Traçabilité des sessions actives pour déconnexion distante et audit de sécurité.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions', verbose_name=_('Utilisateur'))
    session_key = models.CharField(_('Clé de session'), max_length=40, unique=True)
    ip_address = models.GenericIPAddressField(_('Adresse IP'), null=True, blank=True)
    user_agent = models.CharField(_('User Agent'), max_length=255, blank=True, null=True)
    last_activity = models.DateTimeField(_('Dernière activité'), auto_now=True)
    
    class Meta(BaseModel.Meta):
        verbose_name = _('Session Utilisateur')
        verbose_name_plural = _('Sessions Utilisateurs')
        db_table = 'accounts_user_session'

    def __str__(self) -> str:
        return f"Session {self.session_key} - {self.user.email}"


class AuditUser(BaseModel):
    """
    Journal d'audit immuable des actions critiques (connexion, changement de mot de passe, etc.).
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='audit_trails', verbose_name=_('Utilisateur'))
    action = models.CharField(_('Action'), max_length=50) # ex: LOGIN, LOGOUT, PASSWORD_CHANGE
    ip_address = models.GenericIPAddressField(_('Adresse IP'), null=True, blank=True)
    details = models.JSONField(_('Détails supplémentaires'), default=dict)

    class Meta(BaseModel.Meta):
        verbose_name = _('Audit Utilisateur')
        verbose_name_plural = _('Audits Utilisateurs')
        db_table = 'accounts_audit_user'

    def __str__(self) -> str:
        return f"{self.action} - {self.user.email} ({self.created_at})"
