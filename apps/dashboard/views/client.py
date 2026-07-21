from django.views.generic import TemplateView, ListView, DetailView
from django.shortcuts import get_object_or_404
from apps.core.mixins import ClientRequiredMixin
from apps.reservations.services.selectors import ReservationSelector
from apps.payments.services.selectors import PaymentSelector

class ClientDashboardView(ClientRequiredMixin, TemplateView):
    template_name = 'pages/dashboard/client/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Assuming there are selectors to get summary statistics for client
        context['recent_reservations'] = ReservationSelector.get_client_reservations(self.request.user)[:5]
        return context

class ClientReservationsView(ClientRequiredMixin, ListView):
    template_name = 'pages/dashboard/client/reservations.html'
    context_object_name = 'reservations'
    paginate_by = 10

    def get_queryset(self):
        return ReservationSelector.get_client_reservations(self.request.user)

class ClientReservationDetailView(ClientRequiredMixin, DetailView):
    template_name = 'pages/dashboard/client/reservation_detail.html'
    context_object_name = 'reservation'

    def get_object(self):
        return get_object_or_404(
            ReservationSelector.get_client_reservations(self.request.user),
            pk=self.kwargs.get('pk')
        )

class ClientFavoritesView(ClientRequiredMixin, ListView):
    template_name = 'pages/dashboard/client/favorites.html'
    context_object_name = 'favorites'
    paginate_by = 12

    def get_queryset(self):
        # Placeholder if there is a favorite selector
        return []

class ClientPaymentsView(ClientRequiredMixin, ListView):
    template_name = 'pages/dashboard/client/payments.html'
    context_object_name = 'payments'
    paginate_by = 10

    def get_queryset(self):
        return PaymentSelector.get_client_payments(self.request.user)

class ClientInvoicesView(ClientRequiredMixin, TemplateView):
    template_name = 'pages/dashboard/client/invoices.html'

class ClientDocumentsView(ClientRequiredMixin, TemplateView):
    template_name = 'pages/dashboard/client/documents.html'

class ClientHistoryView(ClientRequiredMixin, TemplateView):
    template_name = 'pages/dashboard/client/history.html'

class ClientProfileView(ClientRequiredMixin, TemplateView):
    template_name = 'pages/dashboard/client/profile.html'

class ClientSecurityView(ClientRequiredMixin, TemplateView):
    template_name = 'pages/dashboard/client/security.html'

class ClientSettingsView(ClientRequiredMixin, TemplateView):
    template_name = 'pages/dashboard/client/settings.html'

class ClientSupportView(ClientRequiredMixin, TemplateView):
    template_name = 'pages/dashboard/client/support.html'
