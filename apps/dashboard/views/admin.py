from django.views.generic import TemplateView, ListView, DetailView
from apps.core.mixins import AdminRequiredMixin
from apps.accounts.services.selectors import UserSelector
from apps.properties.services.selectors import PropertySelector
from apps.reservations.services.selectors import ReservationSelector
from apps.payments.services.selectors import PaymentSelector

class AdminDashboardView(AdminRequiredMixin, TemplateView):
    template_name = 'pages/dashboard/admin/home.html'

class AdminValidateOwnersView(AdminRequiredMixin, ListView):
    template_name = 'pages/dashboard/admin/validate_owners.html'
    context_object_name = 'owners'
    paginate_by = 20

    def get_queryset(self):
        # Fetch pending owners
        return []

class AdminValidatePropertiesView(AdminRequiredMixin, ListView):
    template_name = 'pages/dashboard/admin/validate_properties.html'
    context_object_name = 'properties'
    paginate_by = 20

    def get_queryset(self):
        # Fetch pending properties
        return PropertySelector.get_pending_properties()

class AdminClientsView(AdminRequiredMixin, ListView):
    template_name = 'pages/dashboard/admin/clients.html'
    context_object_name = 'clients'
    paginate_by = 20

    def get_queryset(self):
        return []

class AdminOwnersView(AdminRequiredMixin, ListView):
    template_name = 'pages/dashboard/admin/owners.html'
    context_object_name = 'owners'
    paginate_by = 20

    def get_queryset(self):
        return []

class AdminReservationsView(AdminRequiredMixin, ListView):
    template_name = 'pages/dashboard/admin/reservations.html'
    context_object_name = 'reservations'
    paginate_by = 20

    def get_queryset(self):
        return []

class AdminPaymentsView(AdminRequiredMixin, ListView):
    template_name = 'pages/dashboard/admin/payments.html'
    context_object_name = 'payments'
    paginate_by = 20

    def get_queryset(self):
        return []

class AdminPayoutsView(AdminRequiredMixin, ListView):
    template_name = 'pages/dashboard/admin/payouts.html'
    context_object_name = 'payouts'
    paginate_by = 20

    def get_queryset(self):
        return []

class AdminDocumentsView(AdminRequiredMixin, TemplateView):
    template_name = 'pages/dashboard/admin/documents.html'

class AdminSupportView(AdminRequiredMixin, TemplateView):
    template_name = 'pages/dashboard/admin/support.html'

class AdminDisputesView(AdminRequiredMixin, TemplateView):
    template_name = 'pages/dashboard/admin/disputes.html'

class AdminAnalyticsView(AdminRequiredMixin, TemplateView):
    template_name = 'pages/dashboard/admin/analytics.html'

class AdminConfigurationView(AdminRequiredMixin, TemplateView):
    template_name = 'pages/dashboard/admin/config.html'

class AdminLogsView(AdminRequiredMixin, TemplateView):
    template_name = 'pages/dashboard/admin/logs.html'

class AdminProfileView(AdminRequiredMixin, TemplateView):
    template_name = 'pages/dashboard/admin/profile.html'

class AdminSecurityView(AdminRequiredMixin, TemplateView):
    template_name = 'pages/dashboard/admin/security.html'

class AdminSettingsView(AdminRequiredMixin, TemplateView):
    template_name = 'pages/dashboard/admin/settings.html'
