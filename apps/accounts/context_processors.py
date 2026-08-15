from django.conf import settings


def social_login(request):
    """Expose quels boutons de connexion sociale afficher : tant que
    GOOGLE_CLIENT_ID/SECRET ne sont pas configurés dans .env, le bouton Google
    reste masqué plutôt que d'afficher un lien qui échouerait au clic."""
    google_app = settings.SOCIALACCOUNT_PROVIDERS.get('google', {}).get('APP', {})
    return {
        'google_login_enabled': bool(google_app.get('client_id') and google_app.get('secret')),
    }
