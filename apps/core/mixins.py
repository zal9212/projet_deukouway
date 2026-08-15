from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied, ValidationError, ObjectDoesNotExist, SuspiciousOperation
from django.http import Http404
from django.shortcuts import redirect, render
from django.contrib import messages
import logging

logger = logging.getLogger(__name__)

class ClientRequiredMixin(AccessMixin):
    """Vérifie que l'utilisateur est un client connecté."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not getattr(request.user, 'is_client', False):
            messages.error(request, "Accès réservé aux clients/locataires.")
            return redirect('public:home')
        return super().dispatch(request, *args, **kwargs)

class OwnerRequiredMixin(AccessMixin):
    """Vérifie que l'utilisateur est un propriétaire connecté."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not getattr(request.user, 'is_owner', False):
            messages.error(request, "Accès réservé aux propriétaires.")
            return redirect('public:home')
        return super().dispatch(request, *args, **kwargs)

class AdminRequiredMixin(AccessMixin):
    """Vérifie que l'utilisateur est un SuperAdmin ou membre du staff."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not (request.user.is_staff or request.user.is_superuser or getattr(request.user, 'is_superadmin', False)):
            raise PermissionDenied("Accès réservé exclusivement aux administrateurs.")
        return super().dispatch(request, *args, **kwargs)

class ViewExceptionHandlingMixin:
    """
    Mixin de gestion robuste des exceptions pour les vues Web.
    Attrape ValidationError, ObjectDoesNotExist, PermissionDenied, SuspiciousOperation, Http404.
    """
    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except PermissionDenied as e:
            logger.warning(f"PermissionDenied dans {self.__class__.__name__}: {e}")
            messages.error(request, str(e) or "Accès refusé.")
            return render(request, '403.html', status=403)
        except ValidationError as e:
            logger.warning(f"ValidationError dans {self.__class__.__name__}: {e}")
            messages.error(request, e.message if hasattr(e, 'message') else str(e))
            return redirect(request.META.get('HTTP_REFERER', 'public:home'))
        except (ObjectDoesNotExist, Http404) as e:
            logger.info(f"Objet non trouvé dans {self.__class__.__name__}: {e}")
            return render(request, '404.html', status=404)
        except SuspiciousOperation as e:
            logger.error(f"SuspiciousOperation détectée dans {self.__class__.__name__}: {e}")
            messages.error(request, "Opération non autorisée détectée.")
            return redirect('public:home')
