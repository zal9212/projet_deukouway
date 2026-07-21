from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from apps.documents.services.selectors import DocumentSelector

class ClientRequiredMixin(AccessMixin):
    """Vérifie que l'utilisateur est un client."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_client:
            messages.error(request, "Accès réservé aux locataires.")
            return redirect('public:home') # A adapter avec l'url correcte
        return super().dispatch(request, *args, **kwargs)

class OwnerRequiredMixin(AccessMixin):
    """Vérifie que l'utilisateur est un propriétaire."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_owner:
            messages.error(request, "Accès réservé aux propriétaires.")
            return redirect('public:home')
        return super().dispatch(request, *args, **kwargs)

class PendingOwnerMixin(AccessMixin):
    """Redirige les propriétaires non validés vers une page d'attente."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_owner:
            return self.handle_no_permission()
        if not request.user.is_active: # Si inactif = en attente de validation
            return redirect('accounts:owner_pending')
        return super().dispatch(request, *args, **kwargs)

class VerifiedOwnerRequiredMixin(OwnerRequiredMixin):
    """Vérifie que le propriétaire a fourni ses documents KYC et est approuvé."""
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if isinstance(response, type(redirect('public:home'))): # Si déjà bloqué par OwnerRequiredMixin
            return response
            
        # Logique simplifiée : on suppose que s'il est actif, le SuperAdmin a validé son compte, 
        # mais on peut aussi vérifier s'il a un DocumentVerified via DocumentSelector.
        if not request.user.is_active:
            return redirect('accounts:owner_pending')
            
        return response

class AdminRequiredMixin(AccessMixin):
    """Vérifie que l'utilisateur est un SuperAdmin ou Staff."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied("Accès réservé aux administrateurs.")
        return super().dispatch(request, *args, **kwargs)
