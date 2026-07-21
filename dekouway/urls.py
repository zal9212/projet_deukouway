from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls', namespace='public')),
    path('auth/', include('apps.accounts.urls', namespace='accounts')),
    path('logements/', include('apps.properties.urls', namespace='properties')),
    path('dashboard/', include('apps.dashboard.urls', namespace='dashboard')),
]

handler403 = 'apps.core.views.errors.handler403'
handler404 = 'apps.core.views.errors.handler404'
handler500 = 'apps.core.views.errors.handler500'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
