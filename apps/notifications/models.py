from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel

class Notification(BaseModel):
    """
    Notification intégrée (In-App) pour un utilisateur.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications', verbose_name=_('Utilisateur'))
    title = models.CharField(_('Titre'), max_length=255)
    message = models.TextField(_('Message'))
    is_read = models.BooleanField(_('Est lu'), default=False)
    read_at = models.DateTimeField(_('Date de lecture'), null=True, blank=True)
    link = models.URLField(_('Lien de redirection'), blank=True, null=True)

    class Meta(BaseModel.Meta):
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        db_table = 'notifications_notification'

    def __str__(self) -> str:
        return f"Notification pour {self.user.email} - {self.title}"

class NotificationPreference(BaseModel):
    """
    Préférences de l'utilisateur pour les canaux de notification.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_preferences', verbose_name=_('Utilisateur'))
    email_enabled = models.BooleanField(_('Activer Email'), default=True)
    sms_enabled = models.BooleanField(_('Activer SMS'), default=False)
    push_enabled = models.BooleanField(_('Activer Push (In-App)'), default=True)

    class Meta(BaseModel.Meta):
        verbose_name = _('Préférence de Notification')
        verbose_name_plural = _('Préférences de Notifications')
        db_table = 'notifications_preference'

    def __str__(self) -> str:
        return f"Préférences de {self.user.email}"

class NotificationHistory(BaseModel):
    """
    Audit de l'envoi des notifications via des services externes (Email, SMS).
    """
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='history', verbose_name=_('Notification d\'origine'))
    channel = models.CharField(_('Canal d\'envoi'), max_length=50) # ex: EMAIL, SMS, PUSH
    status = models.CharField(_('Statut de l\'envoi'), max_length=50) # ex: SENT, FAILED
    error_message = models.TextField(_('Message d\'erreur (si échec)'), blank=True)

    class Meta(BaseModel.Meta):
        verbose_name = _('Historique d\'envoi de Notification')
        verbose_name_plural = _('Historiques d\'envoi de Notifications')
        db_table = 'notifications_history'

    def __str__(self) -> str:
        return f"Envoi {self.channel} - {self.status}"
