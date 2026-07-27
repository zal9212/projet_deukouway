from django.views.generic import TemplateView, ListView, DetailView, FormView, View
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.http import Http404

from apps.core.mixins import ClientRequiredMixin, ViewExceptionHandlingMixin
from apps.reservations.services.selectors import ReservationSelector
from apps.payments.services.selectors import PaymentSelector
from apps.properties.services.selectors import PropertySelector
from apps.documents.services.selectors import DocumentSelector
from apps.support.services.selectors import TicketSelector
from apps.accounts.services.selectors import UserSelector
from apps.dashboard.services.selectors import DashboardSelector
from apps.notifications.services.selectors import NotificationSelector

from apps.accounts.services.services import AccountService
from apps.accounts.services.exceptions import UserAlreadyExists
from apps.support.services.services import SupportService
from apps.documents.services.services import DocumentService
from apps.notifications.services.services import NotificationService

class ClientDashboardView(ClientRequiredMixin, ViewExceptionHandlingMixin, TemplateView):
    template_name = 'pages/dashboard/client/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = str(self.request.user.id)
        context['stats'] = DashboardSelector.get_client_stats(user_id)
        context['recent_reservations'] = ReservationSelector.get_client_reservations(user_id)[:5]
        context['activities'] = DashboardSelector.get_recent_activity(user_id, limit=5)
        return context

class ClientReservationsView(ClientRequiredMixin, ViewExceptionHandlingMixin, ListView):
    template_name = 'pages/dashboard/client/reservations.html'
    context_object_name = 'reservations'
    paginate_by = 10

    def get_queryset(self):
        search_query = self.request.GET.get('search', '').strip()
        status_filter = self.request.GET.get('status', '').strip()
        return ReservationSelector.get_client_reservations(
            str(self.request.user.id), search_query=search_query, status=status_filter
        )

class ClientReservationDetailView(ClientRequiredMixin, ViewExceptionHandlingMixin, DetailView):
    template_name = 'pages/dashboard/client/reservation_detail.html'
    context_object_name = 'reservation'

    def get_object(self, queryset=None):
        res_id = self.kwargs.get('pk') or self.kwargs.get('id')
        res = ReservationSelector.get_reservation_by_id(str(res_id))
        if not res or str(res.client.id) != str(self.request.user.id):
            raise Http404("Réservation introuvable.")
        return res

class ClientFavoritesView(ClientRequiredMixin, ViewExceptionHandlingMixin, ListView):
    template_name = 'pages/dashboard/client/favorites.html'
    context_object_name = 'favorites'
    paginate_by = 12

    def get_queryset(self):
        return PropertySelector.get_user_favorites(str(self.request.user.id))

class ClientPaymentsView(ClientRequiredMixin, ViewExceptionHandlingMixin, ListView):
    template_name = 'pages/dashboard/client/payments.html'
    context_object_name = 'payments'
    paginate_by = 10

    def get_queryset(self):
        return PaymentSelector.get_client_payments(str(self.request.user.id))

class ClientInvoicesView(ClientRequiredMixin, ViewExceptionHandlingMixin, ListView):
    template_name = 'pages/dashboard/client/payments.html'
    context_object_name = 'invoices'
    paginate_by = 10

    def get_queryset(self):
        return PaymentSelector.get_client_invoices(str(self.request.user.id))

class ClientPaymentsExportView(ClientRequiredMixin, ViewExceptionHandlingMixin, View):
    def get(self, request, *args, **kwargs):
        import csv
        from django.http import HttpResponse

        payments = PaymentSelector.get_client_payments(str(request.user.id))
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="mes_paiements_dekouway.csv"'
        writer = csv.writer(response)
        writer.writerow(['Logement', 'Réservation', 'Date', 'Méthode', 'Montant', 'Devise', 'Statut'])
        for payment in payments:
            writer.writerow([
                payment.reservation.property.title,
                payment.reservation.confirmation_code or str(payment.reservation.id)[:8],
                payment.created_at.strftime('%Y-%m-%d'),
                payment.get_method_display(),
                payment.amount,
                payment.currency,
                payment.get_status_display(),
            ])
        return response

class ClientDocumentsView(ClientRequiredMixin, ViewExceptionHandlingMixin, ListView):
    template_name = 'pages/dashboard/client/documents.html'
    context_object_name = 'documents'
    paginate_by = 10

    def get_queryset(self):
        return DocumentSelector.get_user_documents(str(self.request.user.id))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = DocumentSelector.get_all_categories()
        return context

    def post(self, request, *args, **kwargs):
        title = request.POST.get('title', '')
        category_id = request.POST.get('category')
        file_obj = request.FILES.get('file')
        category = DocumentSelector.get_all_categories().filter(id=category_id).first()
        if file_obj and category:
            DocumentService.upload(request.user, category, title or file_obj.name, file_obj)
            messages.success(request, "Document téléchargé avec succès !")
        else:
            messages.error(request, "Veuillez sélectionner une catégorie et un fichier valides.")
        return redirect('dashboard:client_documents')

class ClientHistoryView(ClientRequiredMixin, ViewExceptionHandlingMixin, ListView):
    template_name = 'pages/dashboard/client/history.html'
    context_object_name = 'audit_logs'
    paginate_by = 15

    def get_queryset(self):
        return UserSelector.get_user_audit_logs(str(self.request.user.id))

class ClientProfileView(ClientRequiredMixin, ViewExceptionHandlingMixin, TemplateView):
    template_name = 'pages/dashboard/client/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = UserSelector.get_user_profile(str(self.request.user.id))
        return context

    def post(self, request, *args, **kwargs):
        new_email = request.POST.get('email')
        if new_email and new_email != request.user.email:
            try:
                AccountService.change_email(request.user, new_email)
                messages.success(request, "Adresse email mise à jour.")
            except UserAlreadyExists:
                messages.error(request, "Cet email est déjà utilisé par un autre compte.")

        profile = UserSelector.get_user_profile(request.user)
        profile.first_name = request.POST.get('first-name', profile.first_name)
        profile.last_name = request.POST.get('last-name', profile.last_name)
        profile.phone = request.POST.get('phone', profile.phone)
        profile.save(update_fields=['first_name', 'last_name', 'phone'])

        messages.info(request, "Informations de profil enregistrées.")
        return redirect('dashboard:client_profile')

class ClientSecurityView(ClientRequiredMixin, ViewExceptionHandlingMixin, TemplateView):
    template_name = 'pages/dashboard/client/security.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sessions'] = UserSelector.get_user_sessions(str(self.request.user.id))
        return context

    def post(self, request, *args, **kwargs):
        current_password = request.POST.get('current_password', '')
        new_pass = request.POST.get('new_password', '')

        if not request.user.check_password(current_password):
            messages.error(request, "Le mot de passe actuel est incorrect.")
        elif len(new_pass) < 8:
            messages.error(request, "Le nouveau mot de passe doit contenir au moins 8 caractères.")
        else:
            AccountService.change_password(request.user, new_pass)
            update_session_auth_hash(request, request.user)
            messages.success(request, "Mot de passe modifié avec succès.")
        return redirect('dashboard:client_security')

class ClientSettingsView(ClientRequiredMixin, ViewExceptionHandlingMixin, TemplateView):
    template_name = 'pages/dashboard/client/settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['preferences'] = NotificationSelector.get_or_create_preferences(self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        NotificationService.update_preferences(
            request.user,
            email_enabled=bool(request.POST.get('email_enabled')),
            sms_enabled=bool(request.POST.get('sms_enabled')),
        )
        messages.success(request, "Préférences de notification enregistrées.")
        return redirect('dashboard:client_settings')

class ClientSupportView(ClientRequiredMixin, ViewExceptionHandlingMixin, ListView):
    template_name = 'pages/dashboard/client/help.html'
    context_object_name = 'tickets'
    paginate_by = 10

    def get_queryset(self):
        return TicketSelector.get_user_tickets(str(self.request.user.id))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = TicketSelector.get_categories()
        return context

    def post(self, request, *args, **kwargs):
        category_id = request.POST.get('category')
        subject = request.POST.get('subject', '').strip()
        description = request.POST.get('message', '').strip()
        category = TicketSelector.get_categories().filter(id=category_id).first()
        if category and subject and description:
            SupportService.create_ticket(request.user, category, subject, description)
            messages.success(request, "Votre message a été envoyé au support.")
        else:
            messages.error(request, "Veuillez renseigner un sujet, une catégorie et un message.")
        return redirect('dashboard:client_support')
