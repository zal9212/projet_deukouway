from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    # OpenAPI Schema & Documentation Swagger/ReDoc
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # REST Modules
    path('accounts/', include('apps.accounts.api.urls')),
    path('properties/', include('apps.properties.api.urls')),
    path('reservations/', include('apps.reservations.api.urls')),
    path('payments/', include('apps.payments.api.urls')),
    path('notifications/', include('apps.notifications.api.urls')),
    path('documents/', include('apps.documents.api.urls')),
    path('support/', include('apps.support.api.urls')),
    path('dashboard/', include('apps.dashboard.api.urls')),
    path('ai/', include('apps.ai.api.urls')),
]
