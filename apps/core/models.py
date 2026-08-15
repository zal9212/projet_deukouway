import uuid
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class BaseModel(models.Model):
    """
    Abstract BaseModel providing UUID, Timestamps, Soft Delete, and Audit trails.
    Every model in DEKOUWAY must inherit from this class to guarantee data consistency
    and compliance with security best practices.
    """
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False,
        verbose_name=_("ID unique (UUID)")
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        db_index=True,
        verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        db_index=True,
        verbose_name=_("Date de dernière modification")
    )
    
    # Audit trail (using string references to avoid circular imports for AUTH_USER_MODEL)
    created_by = models.ForeignKey(
        'accounts.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='%(class)s_created',
        verbose_name=_("Créé par")
    )
    updated_by = models.ForeignKey(
        'accounts.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='%(class)s_updated',
        verbose_name=_("Mis à jour par")
    )
    created_ip = models.GenericIPAddressField(
        null=True, 
        blank=True,
        verbose_name=_("IP de création")
    )
    updated_ip = models.GenericIPAddressField(
        null=True, 
        blank=True,
        verbose_name=_("IP de modification")
    )

    # Soft delete
    is_deleted = models.BooleanField(
        default=False, 
        db_index=True,
        verbose_name=_("Est supprimé (Soft Delete)")
    )
    deleted_at = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name=_("Date de suppression")
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def soft_delete(self) -> None:
        """
        Applique un soft-delete sur l'objet.
        L'objet n'est pas détruit en base, mais marqué comme supprimé.
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def restore(self) -> None:
        """
        Restaure un objet précédemment soft-deleted.
        """
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])
