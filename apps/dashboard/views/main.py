from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect


class DashboardRedirectView(LoginRequiredMixin, View):
    """
    Vue centrale de redirection vers le tableau de bord approprié
    selon le rôle de l'utilisateur (SuperAdmin, Propriétaire, Client).
    """
    def get(self, request, *args, **kwargs):
        user = request.user
        if getattr(user, 'is_superadmin', False) or user.is_staff or user.is_superuser:
            return redirect('dashboard:admin_home')
        elif getattr(user, 'is_owner', False):
            return redirect('dashboard:owner_home')
        return redirect('dashboard:client_home')
