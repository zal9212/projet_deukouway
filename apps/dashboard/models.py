from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel

class AuditLog(BaseModel):
    """
    Centralized logging for critical business actions (Global SuperAdmin audit).
    This tracks WHO did WHAT to WHICH entity.
    """
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='audit_logs', verbose_name=_('Acteur'))
    action = models.CharField(_('Action effectuée'), max_length=255, db_index=True)
    entity_type = models.CharField(_('Type d\'entité affectée'), max_length=100) # ex: 'Property', 'Reservation'
    entity_id = models.UUIDField(_('ID de l\'entité'), null=True, blank=True)
    changes = models.JSONField(_('Détail des modifications'), default=dict)
    ip_address = models.GenericIPAddressField(_('Adresse IP'), null=True, blank=True)

    class Meta(BaseModel.Meta):
        verbose_name = _('Journal d\'Audit (Global)')
        verbose_name_plural = _('Journaux d\'Audit (Global)')
        db_table = 'dashboard_audit_log'

    def __str__(self) -> str:
        return f"{self.action} par {self.actor.email if self.actor else 'Système'} sur {self.entity_type}"

class ActivityLog(BaseModel):
    """
    General activity log to display to the user in their own dashboard.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='activity_logs', verbose_name=_('Utilisateur'))
    description = models.TextField(_('Description de l\'activité'))
    is_public = models.BooleanField(_('Visible publiquement'), default=False)

    class Meta(BaseModel.Meta):
        verbose_name = _('Journal d\'Activité Utilisateur')
        verbose_name_plural = _('Journaux d\'Activité Utilisateur')
        db_table = 'dashboard_activity_log'

    def __str__(self) -> str:
        return f"Activité de {self.user.email} - {self.created_at}"

class SystemLog(BaseModel):
    """
    Technical logs (e.g., third-party API failures like Stripe, Wave, Orange Money).
    """
    level = models.CharField(_('Niveau (Gravité)'), max_length=20, db_index=True) # INFO, WARNING, ERROR, CRITICAL
    source = models.CharField(_('Source / Module'), max_length=100) # WAVE_API, STRIPE_API, INTERNAL
    message = models.TextField(_('Message'))
    traceback = models.TextField(_('Traceback (Stack trace)'), blank=True)

    class Meta(BaseModel.Meta):
        verbose_name = _('Journal Système (Technique)')
        verbose_name_plural = _('Journaux Système (Technique)')
        db_table = 'dashboard_system_log'

    def __str__(self) -> str:
        return f"[{self.level}] {self.source} - {self.created_at}"
