from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView
from apps.core.views.public import HomeView, SearchView, FAQView
from apps.accounts.views.auth import CustomLoginView, CustomLogoutView, ClientRegisterView, OwnerRegisterView, RegisterChoiceView
from apps.dashboard.views.main import DashboardRedirectView
from apps.dashboard.views.client import ClientProfileView
from apps.core.views.health import health_check_view
from apps.core.views.metrics import metrics_view

urlpatterns = [
    path('health/', health_check_view, name='health_check'),
    path('metrics/', metrics_view, name='metrics'),
    path('admin/', admin.site.urls),
    path('api/v1/', include('apps.api.urls')),
    # django-allauth : uniquement pour la connexion Google (voir apps/accounts/adapters.py).
    # Nos propres vues restent la seule voie pour login/inscription par email.
    path('accounts/', include('allauth.urls')),
    path('', HomeView.as_view(), name='home'),
    path('annonces/', SearchView.as_view(), name='properties_list'),
    path('support/', FAQView.as_view(), name='support'),
    path('reservations/', include('apps.reservations.urls')),  # définit déjà name='bookings_list'
    path('paiements/', include('apps.payments.urls')),
    path('se-connecter/', CustomLoginView.as_view(), name='login'),
    path('se-deconnecter/', CustomLogoutView.as_view(), name='logout'),
    path('rejoindre/', RegisterChoiceView.as_view(), name='register_choice'),
    path('rejoindre/voyageur/', ClientRegisterView.as_view(), name='register_client'),
    path('rejoindre/hote/', OwnerRegisterView.as_view(), name='register_owner'),
    path('mon-compte/', ClientProfileView.as_view(), name='profile'),

    path('', include('apps.core.urls', namespace='public')),
    path('auth/', include('apps.accounts.urls', namespace='accounts')),
    path('support/', include('apps.support.urls', namespace='support')),
    path('notifications/', include('apps.notifications.urls', namespace='notifications')),
    path('portail/', include('apps.dashboard.urls', namespace='dashboard')),
    path('dashboard/', RedirectView.as_view(pattern_name='dashboard:home', permanent=False)),
    path('dashboard/owner/', RedirectView.as_view(pattern_name='dashboard:owner_home', permanent=False)),
    path('dashboard/superadmin/', RedirectView.as_view(pattern_name='dashboard:admin_home', permanent=False)),
    path('dashboard/client/', RedirectView.as_view(pattern_name='dashboard:client_home', permanent=False)),
    path('tableau-de-bord/', DashboardRedirectView.as_view(), name='dashboard_redirect'),
]

handler403 = 'apps.core.views.errors.handler403'
handler404 = 'apps.core.views.errors.handler404'
handler500 = 'apps.core.views.errors.handler500'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
