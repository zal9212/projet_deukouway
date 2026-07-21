from django.urls import path, include
from .views.client import (
    ClientDashboardView, ClientReservationsView, ClientReservationDetailView,
    ClientFavoritesView, ClientPaymentsView, ClientInvoicesView,
    ClientDocumentsView, ClientHistoryView, ClientProfileView,
    ClientSecurityView, ClientSettingsView, ClientSupportView
)
from .views.owner import (
    OwnerDashboardView, OwnerPropertiesView, OwnerAddPropertyView,
    OwnerEditPropertyView, OwnerCalendarView, OwnerRequestsView,
    OwnerRequestDetailView, OwnerPayoutsView, OwnerStatsView,
    OwnerDocumentsView, OwnerProfileView, OwnerSecurityView,
    OwnerSettingsView, OwnerSupportView
)
from .views.admin import (
    AdminDashboardView, AdminValidateOwnersView, AdminValidatePropertiesView,
    AdminClientsView, AdminOwnersView, AdminReservationsView,
    AdminPaymentsView, AdminPayoutsView, AdminDocumentsView,
    AdminSupportView, AdminDisputesView, AdminAnalyticsView,
    AdminConfigurationView, AdminLogsView, AdminProfileView,
    AdminSecurityView, AdminSettingsView
)

app_name = 'dashboard'

client_patterns = [
    path('', ClientDashboardView.as_view(), name='client_home'),
    path('reservations/', ClientReservationsView.as_view(), name='client_reservations'),
    path('reservations/<uuid:pk>/', ClientReservationDetailView.as_view(), name='client_reservation_detail'),
    path('favoris/', ClientFavoritesView.as_view(), name='client_favorites'),
    path('paiements/', ClientPaymentsView.as_view(), name='client_payments'),
    path('factures/', ClientInvoicesView.as_view(), name='client_invoices'),
    path('documents/', ClientDocumentsView.as_view(), name='client_documents'),
    path('historique/', ClientHistoryView.as_view(), name='client_history'),
    path('profil/', ClientProfileView.as_view(), name='client_profile'),
    path('securite/', ClientSecurityView.as_view(), name='client_security'),
    path('parametres/', ClientSettingsView.as_view(), name='client_settings'),
    path('support/', ClientSupportView.as_view(), name='client_support'),
]

owner_patterns = [
    path('', OwnerDashboardView.as_view(), name='owner_home'),
    path('logements/', OwnerPropertiesView.as_view(), name='owner_properties'),
    path('logements/ajouter/', OwnerAddPropertyView.as_view(), name='owner_add_property'),
    path('logements/<uuid:pk>/modifier/', OwnerEditPropertyView.as_view(), name='owner_edit_property'),
    path('calendrier/', OwnerCalendarView.as_view(), name='owner_calendar'),
    path('demandes/', OwnerRequestsView.as_view(), name='owner_requests'),
    path('demandes/<uuid:pk>/', OwnerRequestDetailView.as_view(), name='owner_request_detail'),
    path('versements/', OwnerPayoutsView.as_view(), name='owner_payouts'),
    path('statistiques/', OwnerStatsView.as_view(), name='owner_stats'),
    path('documents/', OwnerDocumentsView.as_view(), name='owner_documents'),
    path('profil/', OwnerProfileView.as_view(), name='owner_profile'),
    path('securite/', OwnerSecurityView.as_view(), name='owner_security'),
    path('parametres/', OwnerSettingsView.as_view(), name='owner_settings'),
    path('support/', OwnerSupportView.as_view(), name='owner_support'),
]

admin_patterns = [
    path('', AdminDashboardView.as_view(), name='admin_home'),
    path('validation/proprietaires/', AdminValidateOwnersView.as_view(), name='admin_validate_owners'),
    path('validation/logements/', AdminValidatePropertiesView.as_view(), name='admin_validate_properties'),
    path('clients/', AdminClientsView.as_view(), name='admin_clients'),
    path('proprietaires/', AdminOwnersView.as_view(), name='admin_owners'),
    path('reservations/', AdminReservationsView.as_view(), name='admin_reservations'),
    path('paiements/', AdminPaymentsView.as_view(), name='admin_payments'),
    path('versements/', AdminPayoutsView.as_view(), name='admin_payouts'),
    path('documents/', AdminDocumentsView.as_view(), name='admin_documents'),
    path('support/', AdminSupportView.as_view(), name='admin_support'),
    path('litiges/', AdminDisputesView.as_view(), name='admin_disputes'),
    path('analytics/', AdminAnalyticsView.as_view(), name='admin_analytics'),
    path('configuration/', AdminConfigurationView.as_view(), name='admin_config'),
    path('logs/', AdminLogsView.as_view(), name='admin_logs'),
    path('profil/', AdminProfileView.as_view(), name='admin_profile'),
    path('securite/', AdminSecurityView.as_view(), name='admin_security'),
    path('parametres/', AdminSettingsView.as_view(), name='admin_settings'),
]

urlpatterns = [
    path('client/', include(client_patterns)),
    path('proprietaire/', include(owner_patterns)),
    path('superadmin/', include(admin_patterns)),
]
