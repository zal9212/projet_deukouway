from django.views.generic import TemplateView, ListView, View
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.http import Http404

from apps.core.mixins import AdminRequiredMixin, ViewExceptionHandlingMixin
from apps.accounts.services.selectors import UserSelector
from apps.properties.services.selectors import PropertySelector
from apps.reservations.services.selectors import ReservationSelector
from apps.payments.services.selectors import PaymentSelector
from apps.documents.services.selectors import DocumentSelector
from apps.support.services.selectors import TicketSelector
from apps.support.models import Ticket
from apps.dashboard.services.selectors import DashboardSelector

from apps.accounts.services.services import AccountService
from apps.accounts.services.exceptions import UserAlreadyExists
from apps.properties.services.services import PropertyService
from apps.reservations.services.services import ReservationService
from apps.reservations.services.exceptions import InvalidWorkflowTransition
from apps.payments.services.services import PaymentService
from apps.support.services.services import SupportService

class AdminDashboardView(AdminRequiredMixin, ViewExceptionHandlingMixin, TemplateView):
    template_name = 'pages/dashboard/superadmin/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stats'] = DashboardSelector.get_admin_stats()
        context['pending_owners'] = UserSelector.get_pending_owners()[:5]
        context['pending_properties'] = PropertySelector.get_pending_properties()[:5]
        context['recent_reservations'] = ReservationSelector.get_all_reservations()[:5]
        return context

class AdminValidateOwnersView(AdminRequiredMixin, ViewExceptionHandlingMixin, ListView):
    template_name = 'pages/dashboard/superadmin/owner_validation.html'
    context_object_name = 'pending_owners'
    paginate_by = 10

    def get_queryset(self):
        return UserSelector.get_pending_owners()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_id = self.request.GET.get('id')
        active_owner = self.get_queryset().filter(id=selected_id).first() if selected_id else None
        if not active_owner and context['pending_owners']:
            active_owner = context['pending_owners'][0]
        context['active_owner'] = active_owner
        return context

    def post(self, request, *args, **kwargs):
        owner_id = request.POST.get('owner_id')
        action = request.POST.get('action')
        user = UserSelector.get_user_by_id(owner_id)
        if not user:
            raise Http404("Propriétaire non trouvé.")

        if action == 'approve':
            AccountService.approve_owner(user, admin_user=request.user)
            messages.success(request, f"Le propriétaire {user.email} a été validé et peut désormais publier des logements.")
        elif action == 'reject':
            AccountService.reject_owner(user, admin_user=request.user)
            messages.warning(request, f"Le compte de {user.email} a été rejeté.")
        return redirect('dashboard:admin_validate_owners')

class AdminValidatePropertiesView(AdminRequiredMixin, ViewExceptionHandlingMixin, ListView):
    template_name = 'pages/dashboard/superadmin/property_validation.html'
    context_object_name = 'pending_properties'
    paginate_by = 10

    def get_queryset(self):
        return PropertySelector.get_pending_properties()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_id = self.request.GET.get('id')
        active_prop = self.get_queryset().filter(id=selected_id).first() if selected_id else None
        if not active_prop and context['pending_properties']:
            active_prop = context['pending_properties'][0]
        context['active_prop'] = active_prop
        context['pending_total'] = self.get_queryset().count()
        return context

    def post(self, request, *args, **kwargs):
        prop_id = request.POST.get('property_id')
        action = request.POST.get('action')
        reason = request.POST.get('reason', 'Non conforme')
        prop = PropertySelector.get_property_by_id(prop_id)
        if not prop:
            raise Http404("Logement non trouvé.")

        if action == 'approve':
            PropertyService.approve_property(prop, admin_user=request.user)
            PropertyService.publish_property(prop, owner=prop.owner)
            messages.success(request, f"Le logement '{prop.title}' a été approuvé et publié sur la plateforme.")
        elif action == 'reject':
            PropertyService.reject_property(prop, admin_user=request.user, reason=reason)
            messages.warning(request, f"Le logement '{prop.title}' a été rejeté.")
        return redirect('dashboard:admin_validate_properties')

class AdminClientsView(AdminRequiredMixin, ViewExceptionHandlingMixin, ListView):
    template_name = 'pages/dashboard/superadmin/clients.html'
    context_object_name = 'clients'
    paginate_by = 15

    def get_queryset(self):
        search_query = self.request.GET.get('search', '').strip()
        status_filter = self.request.GET.get('status', '').strip()
        return UserSelector.get_all_clients(search_query=search_query, status=status_filter)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stats'] = DashboardSelector.get_admin_stats()
        return context

    def post(self, request, *args, **kwargs):
        client_id = request.POST.get('client_id')
        action = request.POST.get('action')
        user = UserSelector.get_user_by_id(client_id)
        if not user:
            raise Http404("Client introuvable.")

        if action == 'toggle_status':
            user.is_active = not user.is_active
            user.save(update_fields=['is_active'])
            status_str = "activé" if user.is_active else "bloqué"
            messages.info(request, f"Le compte de {user.email} a été {status_str}.")
        return redirect('dashboard:admin_clients')

class AdminOwnersView(AdminRequiredMixin, ViewExceptionHandlingMixin, ListView):
    template_name = 'pages/dashboard/superadmin/owners.html'
    context_object_name = 'owners'
    paginate_by = 15

    def get_queryset(self):
        search_query = self.request.GET.get('search', '').strip()
        status_filter = self.request.GET.get('status', '').strip()
        return UserSelector.get_all_owners(search_query=search_query, status=status_filter)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stats'] = DashboardSelector.get_admin_stats()
        return context

    def post(self, request, *args, **kwargs):
        owner_id = request.POST.get('owner_id')
        action = request.POST.get('action')
        user = UserSelector.get_user_by_id(owner_id)
        if not user:
            raise Http404("Propriétaire introuvable.")

        if action == 'toggle_status':
            user.is_active = not user.is_active
            user.save(update_fields=['is_active'])
            status_str = "activé" if user.is_active else "bloqué"
            messages.info(request, f"Le compte partenaire de {user.email} a été {status_str}.")
        elif action == 'approve':
            AccountService.approve_owner(user, admin_user=request.user)
            messages.success(request, f"Le compte de {user.email} a été validé.")
        return redirect('dashboard:admin_owners')

class AdminOwnerDetailView(AdminRequiredMixin, ViewExceptionHandlingMixin, TemplateView):
    template_name = 'pages/dashboard/superadmin/owner_detail.html'

    def _get_owner(self):
        owner = UserSelector.get_user_by_id(self.kwargs.get('pk'))
        if not owner or not owner.is_owner:
            raise Http404("Partenaire introuvable.")
        return owner

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        owner = self._get_owner()
        context['owner'] = owner
        context['identity_document'] = owner.identity_documents.order_by('-created_at').first()
        context['properties'] = owner.properties.filter(is_deleted=False).order_by('-created_at')
        return context

    def post(self, request, *args, **kwargs):
        owner = self._get_owner()
        action = request.POST.get('action')

        if action == 'approve':
            AccountService.approve_owner(owner, admin_user=request.user)
            messages.success(request, f"Le compte de {owner.email} a été validé.")
        elif action == 'reject':
            # Le rejet supprime (soft-delete) le compte : le dossier ne sera plus consultable.
            AccountService.reject_owner(owner, admin_user=request.user)
            messages.warning(request, f"Le compte de {owner.email} a été rejeté.")
            return redirect('dashboard:admin_owners')
        elif action == 'toggle_status':
            owner.is_active = not owner.is_active
            owner.save(update_fields=['is_active'])
            status_str = "réactivé" if owner.is_active else "suspendu"
            messages.info(request, f"Le compte partenaire de {owner.email} a été {status_str}.")

        return redirect('dashboard:admin_owner_detail', pk=owner.id)

class AdminValidateReservationsView(AdminRequiredMixin, ViewExceptionHandlingMixin, ListView):
    template_name = 'pages/dashboard/superadmin/reservation_validation.html'
    context_object_name = 'pending_requests'
    paginate_by = 10

    def get_queryset(self):
        return ReservationSelector.get_pending_requests()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_id = self.request.GET.get('id')
        active_req = self.get_queryset().filter(id=selected_id).first() if selected_id else None
        if not active_req and context['pending_requests']:
            active_req = context['pending_requests'][0]
        context['active_req'] = active_req
        return context

    def post(self, request, *args, **kwargs):
        req_id = request.POST.get('request_id')
        action = request.POST.get('action')
        reason = request.POST.get('reason', '')
        req = ReservationSelector.get_request_by_id(req_id)
        if not req:
            raise Http404("Demande de réservation non trouvée.")

        if action == 'approve':
            ReservationService.admin_validate(req, admin_user=request.user)
            messages.success(request, f"La demande de {req.client.email} a été transmise au propriétaire.")
        elif action == 'send_payment_link':
            try:
                ReservationService.admin_send_payment_link(req, admin_user=request.user)
                messages.success(request, f"Le lien de paiement a été envoyé à {req.client.email}.")
            except InvalidWorkflowTransition as exc:
                messages.error(request, str(exc))
        elif action == 'reject':
            ReservationService.admin_reject(req, admin_user=request.user, reason=reason)
            messages.warning(request, f"La demande de {req.client.email} a été rejetée.")
        return redirect('dashboard:admin_validate_reservations')

class AdminReservationsView(AdminRequiredMixin, ViewExceptionHandlingMixin, ListView):
    template_name = 'pages/dashboard/superadmin/reservations.html'
    context_object_name = 'reservations'
    paginate_by = 15

    def get_queryset(self):
        search_query = self.request.GET.get('search', '').strip()
        status_filter = self.request.GET.get('status', '').strip()
        return ReservationSelector.get_all_reservations(search_query=search_query, status=status_filter)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stats'] = DashboardSelector.get_admin_stats()
        return context

    def post(self, request, *args, **kwargs):
        request_id = request.POST.get('request_id')
        action = request.POST.get('action')

        if action == 'contact_owner':
            req = ReservationSelector.get_request_by_id(request_id)
            if not req:
                raise Http404("Demande de réservation non trouvée.")
            try:
                reservation = ReservationService.contact_owner(req, admin_user=request.user)
                messages.success(
                    request,
                    f"Le client {req.client.email} et le propriétaire {req.property.owner.email} ont été mis en contact. "
                    f"Réservation {reservation.confirmation_code} confirmée."
                )
            except InvalidWorkflowTransition as exc:
                messages.error(request, str(exc))

        return redirect('dashboard:admin_reservations')

class AdminPropertiesView(AdminRequiredMixin, ViewExceptionHandlingMixin, ListView):
    template_name = 'pages/dashboard/superadmin/properties.html'
    context_object_name = 'properties'
    paginate_by = 15

    def get_queryset(self):
        search_query = self.request.GET.get('search', '').strip()
        status_filter = self.request.GET.get('status', '').strip()
        return PropertySelector.get_all_properties(search_query=search_query, status=status_filter)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stats'] = DashboardSelector.get_admin_stats()
        return context

class AdminPaymentsView(AdminRequiredMixin, ViewExceptionHandlingMixin, ListView):
    template_name = 'pages/dashboard/superadmin/payments.html'
    context_object_name = 'payments'
    paginate_by = 15

    def get_queryset(self):
        search_query = self.request.GET.get('search', '').strip()
        status_filter = self.request.GET.get('status', '').strip()
        return PaymentSelector.get_all_payments(search_query=search_query, status=status_filter)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stats'] = DashboardSelector.get_admin_stats()
        return context

class AdminPayoutsView(AdminRequiredMixin, ViewExceptionHandlingMixin, ListView):
    template_name = 'pages/dashboard/superadmin/payouts.html'
    context_object_name = 'payouts'
    paginate_by = 15

    def get_queryset(self):
        search_query = self.request.GET.get('search', '').strip()
        status_filter = self.request.GET.get('status', '').strip()
        return PaymentSelector.get_all_payouts(search_query=search_query, status=status_filter)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stats'] = DashboardSelector.get_admin_stats()
        return context

class AdminPaymentDetailView(AdminRequiredMixin, ViewExceptionHandlingMixin, TemplateView):
    template_name = 'pages/dashboard/superadmin/payment_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payment = PaymentSelector.get_payment_by_id(self.kwargs.get('pk'))
        if not payment:
            raise Http404("Paiement introuvable.")
        context['payment'] = payment
        context['history'] = payment.history.order_by('-created_at')
        return context

class AdminPayoutDetailView(AdminRequiredMixin, ViewExceptionHandlingMixin, TemplateView):
    template_name = 'pages/dashboard/superadmin/payout_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payout = PaymentSelector.get_payout_by_id(self.kwargs.get('pk'))
        if not payout:
            raise Http404("Reversement introuvable.")
        context['payout'] = payout
        return context

class AdminDocumentsView(AdminRequiredMixin, ViewExceptionHandlingMixin, ListView):
    template_name = 'pages/dashboard/superadmin/documents.html'
    context_object_name = 'documents'
    paginate_by = 15

    def get_queryset(self):
        search_query = self.request.GET.get('search', '').strip()
        category = self.request.GET.get('category', '').strip()
        return DocumentSelector.get_all_documents(search_query=search_query, category=category)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = DocumentSelector.get_all_categories()
        return context

class AdminSupportView(AdminRequiredMixin, ViewExceptionHandlingMixin, ListView):
    template_name = 'pages/dashboard/superadmin/support_tickets.html'
    context_object_name = 'tickets'
    paginate_by = 15

    def get_queryset(self):
        return TicketSelector.get_all_tickets()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ticket_id = self.request.GET.get('ticket')
        active_ticket = None
        if ticket_id:
            try:
                active_ticket = TicketSelector.get_ticket_by_id(ticket_id)
            except Ticket.DoesNotExist:
                active_ticket = None
        if active_ticket is None:
            active_ticket = context['tickets'].first() if hasattr(context['tickets'], 'first') else (context['tickets'][0] if context['tickets'] else None)
            if active_ticket is not None:
                active_ticket = TicketSelector.get_ticket_by_id(str(active_ticket.id))
        context['active_ticket'] = active_ticket
        return context

    def post(self, request, *args, **kwargs):
        from apps.support.services.exceptions import TicketAlreadyClosed, UnauthorizedTicketAction

        ticket_id = request.POST.get('ticket_id')
        action = request.POST.get('action')
        ticket = TicketSelector.get_ticket_by_id(ticket_id)

        try:
            if action == 'reply':
                content = request.POST.get('content', '').strip()
                if content:
                    SupportService.reply_ticket(ticket, sender=request.user, content=content)
                    messages.success(request, "Réponse envoyée.")
            elif action == 'escalate':
                SupportService.escalate(ticket, admin_user=request.user)
                messages.warning(request, "Ticket escaladé.")
            elif action == 'close':
                SupportService.close_ticket(ticket, user=request.user)
                messages.success(request, "Ticket fermé.")
        except (TicketAlreadyClosed, UnauthorizedTicketAction) as exc:
            messages.error(request, str(exc))

        return redirect(f"{reverse_lazy('dashboard:admin_support')}?ticket={ticket.id}")

class AdminDisputesView(AdminRequiredMixin, ViewExceptionHandlingMixin, ListView):
    template_name = 'pages/dashboard/superadmin/disputes.html'
    context_object_name = 'disputes'
    paginate_by = 15

    def get_queryset(self):
        search_query = self.request.GET.get('search', '').strip()
        status_filter = self.request.GET.get('status', '').strip()
        return TicketSelector.get_disputes(search_query=search_query, status=status_filter)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['open_disputes_count'] = TicketSelector.get_disputes(status='open').count()
        context['resolved_disputes_count'] = TicketSelector.get_disputes(status='resolved').count()
        return context


class AdminResolveDisputeView(AdminRequiredMixin, ViewExceptionHandlingMixin, View):
    """Permet au SuperAdmin d'arbitrer et de trancher un litige financier ou contractuel."""
    def post(self, request, pk, *args, **kwargs):
        from apps.support.models import Dispute
        from django.shortcuts import get_object_or_404

        dispute = get_object_or_404(Dispute, id=pk)
        decision = request.POST.get('decision')
        notes = request.POST.get('resolution_notes', '').strip()

        if not decision:
            messages.error(request, "Veuillez sélectionner une décision arbitrale.")
            return redirect('dashboard:admin_disputes')

        try:
            SupportService.resolve_dispute(
                dispute=dispute,
                decision=decision,
                notes=notes,
                admin_user=request.user
            )
            messages.success(request, f"Le litige a été résolu avec succès ({dispute.get_status_display()}).")
        except Exception as err:
            messages.error(request, f"Erreur lors de la résolution du litige : {err}")

        return redirect('dashboard:admin_disputes')


class AdminAnalyticsView(AdminRequiredMixin, ViewExceptionHandlingMixin, TemplateView):
    template_name = 'pages/dashboard/superadmin/analytics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stats'] = DashboardSelector.get_admin_stats()
        context['ai_analytics'] = DashboardSelector.get_ai_analytics_and_insights()
        return context

class AdminConfigurationView(AdminRequiredMixin, ViewExceptionHandlingMixin, TemplateView):
    template_name = 'pages/dashboard/superadmin/configuration.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['settings'] = PaymentSelector.get_platform_settings()
        return context

    def post(self, request, *args, **kwargs):
        from decimal import Decimal, InvalidOperation
        from django.core.exceptions import ValidationError

        if request.POST.get('form_type') == 'branding':
            try:
                PaymentService.update_branding_settings(
                    site_name=request.POST.get('site_name', '').strip(),
                    logo=request.FILES.get('logo'),
                    hero_image=request.FILES.get('hero_image'),
                )
                messages.success(request, "Identité de la marque mise à jour avec succès.")
            except ValidationError as exc:
                messages.error(request, " ".join(exc.messages))
            return redirect('dashboard:admin_config')

        try:
            commission_percentage = Decimal(request.POST.get('commission_percentage', '0'))
            client_service_fee = Decimal(request.POST.get('client_service_fee', '0'))
            PaymentService.update_platform_settings(commission_percentage, client_service_fee)
            messages.success(request, "Configuration financière mise à jour avec succès.")
        except (InvalidOperation, ValueError):
            messages.error(request, "Valeurs invalides. Veuillez saisir des nombres valides.")
        except ValidationError as exc:
            messages.error(request, " ".join(exc.messages))
        return redirect('dashboard:admin_config')

class AdminLogsView(AdminRequiredMixin, ViewExceptionHandlingMixin, ListView):
    template_name = 'pages/dashboard/superadmin/audit_logs.html'
    context_object_name = 'logs'
    paginate_by = 25

    def get_queryset(self):
        search_query = self.request.GET.get('search', '').strip()
        level = self.request.GET.get('level', '').strip()
        return DashboardSelector.get_system_logs(limit=100, search_query=search_query, level=level)

class AdminLogsExportView(AdminRequiredMixin, ViewExceptionHandlingMixin, View):
    def get(self, request, *args, **kwargs):
        import csv
        from django.http import HttpResponse

        logs = DashboardSelector.get_system_logs(limit=1000)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="journaux_dekouway.csv"'
        writer = csv.writer(response)
        writer.writerow(['Timestamp', 'Niveau', 'Source', 'Message'])
        for log in logs:
            writer.writerow([log.created_at.strftime('%Y-%m-%d %H:%M:%S'), log.level, log.source, log.message])
        return response

class AdminProfileView(AdminRequiredMixin, ViewExceptionHandlingMixin, TemplateView):
    template_name = 'pages/dashboard/superadmin/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = UserSelector.get_user_profile(self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        new_email = request.POST.get('email', '').strip()
        if new_email and new_email != request.user.email:
            try:
                AccountService.change_email(request.user, new_email)
                messages.success(request, "Adresse email mise à jour.")
            except UserAlreadyExists:
                messages.error(request, "Cet email est déjà utilisé par un autre compte.")

        profile = UserSelector.get_user_profile(request.user)
        profile.first_name = request.POST.get('first_name', profile.first_name).strip()
        profile.last_name = request.POST.get('last_name', profile.last_name).strip()
        profile.save(update_fields=['first_name', 'last_name'])

        messages.success(request, "Profil administrateur mis à jour.")
        return redirect('dashboard:admin_profile')

class AdminSecurityView(AdminRequiredMixin, ViewExceptionHandlingMixin, TemplateView):
    template_name = 'pages/dashboard/superadmin/security.html'

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
            messages.success(request, "Mot de passe modifié.")
        return redirect('dashboard:admin_security')

class AdminSettingsView(AdminRequiredMixin, ViewExceptionHandlingMixin, TemplateView):
    template_name = 'pages/dashboard/superadmin/settings.html'

    def post(self, request, *args, **kwargs):
        messages.info(request, "Ces préférences ne sont pas encore modifiables depuis cette interface.")
        return redirect('dashboard:admin_settings')
