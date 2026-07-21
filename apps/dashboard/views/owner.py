from django.views.generic import TemplateView, ListView, DetailView, FormView
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from apps.core.mixins import VerifiedOwnerRequiredMixin
from apps.properties.services.selectors import PropertySelector
from apps.properties.services.services import PropertyService
from apps.reservations.services.selectors import ReservationSelector
from apps.reservations.services.services import ReservationService
from apps.payments.services.selectors import PaymentSelector

class OwnerDashboardView(VerifiedOwnerRequiredMixin, TemplateView):
    template_name = 'pages/dashboard/owner/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # We can add stats here later via selectors
        return context

class OwnerPropertiesView(VerifiedOwnerRequiredMixin, ListView):
    template_name = 'pages/dashboard/owner/properties.html'
    context_object_name = 'properties'
    paginate_by = 10

    def get_queryset(self):
        return PropertySelector.get_owner_properties(self.request.user)

class OwnerAddPropertyView(VerifiedOwnerRequiredMixin, FormView):
    template_name = 'pages/dashboard/owner/add_property.html'
    # Normally we would define a PropertyForm in forms.py
    # We will just redirect for now if valid
    success_url = reverse_lazy('dashboard:owner_properties')
    
    def form_valid(self, form):
        # AccountService logic here
        messages.success(self.request, "Logement ajouté avec succès.")
        return super().form_valid(form)

class OwnerEditPropertyView(VerifiedOwnerRequiredMixin, FormView):
    template_name = 'pages/dashboard/owner/edit_property.html'
    success_url = reverse_lazy('dashboard:owner_properties')

class OwnerCalendarView(VerifiedOwnerRequiredMixin, TemplateView):
    template_name = 'pages/dashboard/owner/calendar.html'

class OwnerRequestsView(VerifiedOwnerRequiredMixin, ListView):
    template_name = 'pages/dashboard/owner/requests.html'
    context_object_name = 'requests'
    paginate_by = 10

    def get_queryset(self):
        # Assumes a selector method exists
        # return ReservationSelector.get_owner_requests(self.request.user)
        return []

class OwnerRequestDetailView(VerifiedOwnerRequiredMixin, DetailView):
    template_name = 'pages/dashboard/owner/request_detail.html'
    context_object_name = 'request'
    
    def get_object(self):
        # Mock object for now
        return None

class OwnerPayoutsView(VerifiedOwnerRequiredMixin, ListView):
    template_name = 'pages/dashboard/owner/payouts.html'
    context_object_name = 'payouts'
    paginate_by = 10

    def get_queryset(self):
        return []

class OwnerStatsView(VerifiedOwnerRequiredMixin, TemplateView):
    template_name = 'pages/dashboard/owner/stats.html'

class OwnerDocumentsView(VerifiedOwnerRequiredMixin, TemplateView):
    template_name = 'pages/dashboard/owner/documents.html'

class OwnerProfileView(VerifiedOwnerRequiredMixin, TemplateView):
    template_name = 'pages/dashboard/owner/profile.html'

class OwnerSecurityView(VerifiedOwnerRequiredMixin, TemplateView):
    template_name = 'pages/dashboard/owner/security.html'

class OwnerSettingsView(VerifiedOwnerRequiredMixin, TemplateView):
    template_name = 'pages/dashboard/owner/settings.html'

class OwnerSupportView(VerifiedOwnerRequiredMixin, TemplateView):
    template_name = 'pages/dashboard/owner/support.html'
