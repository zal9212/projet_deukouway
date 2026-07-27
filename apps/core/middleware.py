import time
import logging
from django.http import HttpResponseForbidden
from django.core.cache import cache

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware:
    """
    Middleware injectant les en-têtes de sécurité renforcés (OWASP Security Headers).
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Content-Security-Policy'] = (
            "default-src 'self' https: data: 'unsafe-inline' 'unsafe-eval'; "
            "img-src 'self' https: data: blob:;"
        )
        return response


class RateLimitMiddleware:
    """
    Middleware de limitation du débit (Rate Limiting anti-Brute Force / anti-Spam).

    Chaque entrée : préfixe de chemin -> (limite de requêtes, fenêtre en secondes).
    Ne s'applique qu'aux méthodes qui modifient un état ou coûtent réellement
    (POST), jamais aux simples GET d'affichage de formulaire.
    """
    LIMITED_PATHS = {
        '/api/v1/accounts/token/': (20, 60),
        '/api/v1/accounts/auth/': (20, 60),
        '/support/chat/': (20, 60),           # assistant IA : chaque appel coûte un appel Groq
        '/api/v1/ai/recommendations/': (20, 60),  # ouvert aux anonymes (AllowAny) mais coûte un appel Groq
        '/api/v1/ai/summary/': (20, 60),          # idem : accessible sans compte, doit rester limité
        '/se-connecter/': (10, 60),          # login web (le brute-force sur l'API l'est déjà)
        '/contact/': (5, 60),                # formulaire de contact public
        '/rejoindre/voyageur/': (10, 60),    # inscription client
        '/rejoindre/hote/': (10, 60),        # inscription propriétaire
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == 'POST':
            for prefix, (max_requests, window_seconds) in self.LIMITED_PATHS.items():
                if request.path.startswith(prefix):
                    ip = self._get_client_ip(request)
                    cache_key = f"rate_limit:{ip}:{prefix}"
                    requests_count = cache.get(cache_key, 0)

                    if requests_count >= max_requests:
                        logger.warning(f"Rate limit dépassé pour l'IP {ip} sur {request.path}")
                        return HttpResponseForbidden("Trop de requêtes. Veuillez patienter avant de réessayer.")

                    cache.set(cache_key, requests_count + 1, timeout=window_seconds)
                    break

        return self.get_response(request)

    def _get_client_ip(self, request):
        # nginx ajoute l'IP réelle du client en DERNIÈRE position via
        # $proxy_add_x_forwarded_for (les valeurs précédentes viennent du client
        # et sont donc falsifiables). Prendre le premier maillon permettrait à
        # n'importe quel client de contourner la limite en forgeant cet en-tête.
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[-1].strip()
        return request.META.get('REMOTE_ADDR', '127.0.0.1')
