from django.urls import path, include
from .views.main import DashboardRedirectView
from .views.client import (
    ClientDashboardView, ClientReservationsView, ClientReservationDetailView,
    ClientFavoritesView, ClientPaymentsView, ClientInvoicesView, ClientPaymentsExportView,
    ClientDocumentsView, ClientHistoryView, ClientProfileView,
    ClientSecurityView, ClientSettingsView, ClientSupportView
)
from .views.owner import (
    OwnerDashboardView, OwnerPropertiesView, OwnerAddPropertyView,
    OwnerEditPropertyView, OwnerCalendarView, OwnerRequestsView,
    OwnerRequestDetailView, OwnerPayoutsView, OwnerPayoutsExportView, OwnerStatsView,
    OwnerDocumentsView, OwnerProfileView, OwnerSecurityView,
    OwnerSettingsView, OwnerSupportView, ResolveMapLinkView
)
from .views.admin import (
    AdminDashboardView, AdminValidateOwnersView, AdminValidatePropertiesView,
    AdminValidateReservationsView,
    AdminClientsView, AdminOwnersView, AdminReservationsView, AdminPropertiesView,
    AdminPaymentsView, AdminPayoutsView, AdminDocumentsView,
    AdminSupportView, AdminDisputesView, AdminAnalyticsView,
    AdminConfigurationView, AdminLogsView, AdminLogsExportView, AdminProfileView,
    AdminSecurityView, AdminSettingsView, AdminOwnerDetailView
)

app_name = 'dashboard'

# ─── Espace Voyageur ─────────────────────────────────────────────────────────
client_patterns = [
    path('', ClientDashboardView.as_view(), name='client_home'),
    path('sejours/', ClientReservationsView.as_view(), name='client_reservations'),
    path('sejours/<uuid:pk>/', ClientReservationDetailView.as_view(), name='client_reservation_detail'),
    path('favoris/', ClientFavoritesView.as_view(), name='client_favorites'),
    path('paiements/', ClientPaymentsView.as_view(), name='client_payments'),
    path('factures/', ClientInvoicesView.as_view(), name='client_invoices'),
    path('paiements/export.csv', ClientPaymentsExportView.as_view(), name='client_payments_export'),
    path('documents/', ClientDocumentsView.as_view(), name='client_documents'),
    path('historique/', ClientHistoryView.as_view(), name='client_history'),
    path('profil/', ClientProfileView.as_view(), name='client_profile'),
    path('securite/', ClientSecurityView.as_view(), name='client_security'),
    path('parametres/', ClientSettingsView.as_view(), name='client_settings'),
    path('assistance/', ClientSupportView.as_view(), name='client_support'),
]

# ─── Espace Hôte ─────────────────────────────────────────────────────────────
owner_patterns = [
    path('', OwnerDashboardView.as_view(), name='owner_home'),
    path('annonces/', OwnerPropertiesView.as_view(), name='owner_properties'),
    path('annonces/nouvelle/', OwnerAddPropertyView.as_view(), name='owner_add_property'),
    path('annonces/resoudre-lien-carte/', ResolveMapLinkView.as_view(), name='owner_resolve_map_link'),
    path('annonces/<uuid:pk>/modifier/', OwnerEditPropertyView.as_view(), name='owner_edit_property'),
    path('planning/', OwnerCalendarView.as_view(), name='owner_calendar'),
    path('demandes/', OwnerRequestsView.as_view(), name='owner_requests'),
    path('demandes/<uuid:pk>/', OwnerRequestDetailView.as_view(), name='owner_request_detail'),
    path('revenus/', OwnerPayoutsView.as_view(), name='owner_payouts'),
    path('revenus/export.csv', OwnerPayoutsExportView.as_view(), name='owner_payouts_export'),
    path('statistiques/', OwnerStatsView.as_view(), name='owner_stats'),
    path('documents/', OwnerDocumentsView.as_view(), name='owner_documents'),
    path('profil/', OwnerProfileView.as_view(), name='owner_profile'),
    path('securite/', OwnerSecurityView.as_view(), name='owner_security'),
    path('parametres/', OwnerSettingsView.as_view(), name='owner_settings'),
    path('assistance/', OwnerSupportView.as_view(), name='owner_support'),
]

# ─── Espace Administration (URLs neutres et non révélatrices) ─────────────────
admin_patterns = [
    path('', AdminDashboardView.as_view(), name='admin_home'),
    path('validation/hotes/', AdminValidateOwnersView.as_view(), name='admin_validate_owners'),
    path('validation/annonces/', AdminValidatePropertiesView.as_view(), name='admin_validate_properties'),
    path('validation/reservations/', AdminValidateReservationsView.as_view(), name='admin_validate_reservations'),
    path('membres/', AdminClientsView.as_view(), name='admin_clients'),
    path('partenaires/', AdminOwnersView.as_view(), name='admin_owners'),
    path('partenaires/<uuid:pk>/', AdminOwnerDetailView.as_view(), name='admin_owner_detail'),
    path('annonces/', AdminPropertiesView.as_view(), name='admin_properties'),
    path('reservations/', AdminReservationsView.as_view(), name='admin_reservations'),
    path('transactions/', AdminPaymentsView.as_view(), name='admin_payments'),
    path('versements/', AdminPayoutsView.as_view(), name='admin_payouts'),
    path('documents/', AdminDocumentsView.as_view(), name='admin_documents'),
    path('tickets/', AdminSupportView.as_view(), name='admin_support'),
    path('litiges/', AdminDisputesView.as_view(), name='admin_disputes'),
    path('tableau-de-bord/', AdminAnalyticsView.as_view(), name='admin_analytics'),
    path('configuration/', AdminConfigurationView.as_view(), name='admin_config'),
    path('journaux/', AdminLogsView.as_view(), name='admin_logs'),
    path('journaux/export.csv', AdminLogsExportView.as_view(), name='admin_logs_export'),
    path('profil/', AdminProfileView.as_view(), name='admin_profile'),
    path('securite/', AdminSecurityView.as_view(), name='admin_security'),
    path('preferences/', AdminSettingsView.as_view(), name='admin_settings'),
]

urlpatterns = [
    path('', DashboardRedirectView.as_view(), name='home'),
    path('espace/', include(client_patterns)),
    path('hote/', include(owner_patterns)),
    path('gestion/', include(admin_patterns)),
    # Routes d'alias directes pour compatibilité (ex: /dashboard/owner/, /dashboard/superadmin/, /dashboard/client/)
    path('client/', include(client_patterns)),
    path('owner/', include(owner_patterns)),
    path('superadmin/', include(admin_patterns)),
]
