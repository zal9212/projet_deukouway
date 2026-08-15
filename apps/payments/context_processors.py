from apps.payments.services.selectors import PaymentSelector


def site_branding(request):
    """Expose les paramètres de marque (nom du site, logo, image hero) à tous les
    templates : navbar, footer et layouts d'auth/dashboard en ont besoin sans que
    chaque vue n'ait à les passer explicitement dans son contexte."""
    return {'platform_settings': PaymentSelector.get_platform_settings()}
