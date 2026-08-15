from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import redirect
from django.views.generic import View

from apps.core.mixins import ViewExceptionHandlingMixin
from apps.notifications.services.selectors import NotificationSelector
from apps.notifications.services.services import NotificationService


class NotificationOpenView(LoginRequiredMixin, ViewExceptionHandlingMixin, View):
    """Marque une notification comme lue puis redirige vers son lien (ou vers la page d'origine)."""

    def get(self, request, pk):
        notif = NotificationSelector.get_user_notifications(request.user).filter(id=pk).first()
        if not notif:
            raise Http404("Notification introuvable.")
        if not notif.is_read:
            NotificationService.mark_as_read(notif)
        return redirect(notif.link or request.META.get('HTTP_REFERER') or 'dashboard:home')


class NotificationMarkAllReadView(LoginRequiredMixin, ViewExceptionHandlingMixin, View):
    def post(self, request):
        NotificationService.mark_all_as_read(request.user)
        return redirect(request.META.get('HTTP_REFERER') or 'dashboard:home')
