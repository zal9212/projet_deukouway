from django.db import models
from django.utils.translation import gettext_lazy as _

class RoleChoices(models.TextChoices):
    CLIENT = 'CLIENT', _('Client')
    OWNER = 'OWNER', _('Propriétaire')
    SUPERADMIN = 'SUPERADMIN', _('SuperAdmin')
