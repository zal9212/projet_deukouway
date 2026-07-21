from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel

class DocumentCategory(BaseModel):
    """
    Catégorie de document légal ou contractuel.
    """
    name = models.CharField(_('Nom'), max_length=100)
    slug = models.SlugField(_('Slug'), unique=True)

    class Meta(BaseModel.Meta):
        verbose_name = _('Catégorie de Document')
        verbose_name_plural = _('Catégories de Documents')
        db_table = 'documents_category'

    def __str__(self) -> str:
        return str(self.name)

class Document(BaseModel):
    """
    Stockage des documents juridiques (Baux, contrats de mandat, etc.).
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='documents', verbose_name=_('Utilisateur concerné'))
    category = models.ForeignKey(DocumentCategory, on_delete=models.PROTECT, verbose_name=_('Catégorie'))
    title = models.CharField(_('Titre'), max_length=255)
    file = models.FileField(
        _('Fichier du document'), 
        upload_to='documents/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'png', 'docx'])]
    )
    is_verified = models.BooleanField(_('Est vérifié'), default=False)

    class Meta(BaseModel.Meta):
        verbose_name = _('Document')
        verbose_name_plural = _('Documents')
        db_table = 'documents_document'

    def __str__(self) -> str:
        return f"{self.title} - {self.user.email}"

class DocumentVerification(BaseModel):
    """
    Trace de vérification d'un document par le SuperAdmin.
    """
    document = models.OneToOneField(Document, on_delete=models.CASCADE, related_name='verification', verbose_name=_('Document vérifié'))
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='document_verifications', verbose_name=_('Vérifié par (SuperAdmin)'))
    status = models.CharField(_('Statut de validation'), max_length=20, default='PENDING') # PENDING, APPROVED, REJECTED
    notes = models.TextField(_('Notes internes (SuperAdmin)'), blank=True)

    class Meta(BaseModel.Meta):
        verbose_name = _('Vérification de Document')
        verbose_name_plural = _('Vérifications de Documents')
        db_table = 'documents_verification'

    def __str__(self) -> str:
        return f"Vérification {self.document.id} - {self.status}"
