from django.contrib import admin
from apps.payments.models import PlatformSettings


@admin.register(PlatformSettings)
class PlatformSettingsAdmin(admin.ModelAdmin):
    list_display = ('commission_percentage', 'client_service_fee', 'updated_at')
