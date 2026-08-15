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
        # default-src 'self' https: autorisait n'importe quelle origine HTTPS (scripts
        # compris) : équivalent à pas de CSP contre le XSS. On restreint aux hôtes
        # réellement utilisés par les templates (CDN unpkg/jsdelivr pour Alpine.js/HTMX/
        # Leaflet/Lucide, Google Fonts). 'unsafe-inline'/'unsafe-eval' restent nécessaires
        # tant que les templates embarquent des <script> inline (ex. leaflet_map.html,
        # chatbot_widget.html) et qu'Alpine.js évalue ses expressions x-data/x-show via
        # Function() — les retirer casserait ces pages sans une migration vers un système
        # de nonce, hors périmètre de ce correctif. img-src reste large (risque faible,
        # ce sont des images) pour couvrir les tuiles CARTO et les visuels de secours.
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://unpkg.com https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://unpkg.com; "
            "font-src 'self' https://fonts.gstatic.com data:; "
            "img-src 'self' https: data: blob:; "
            "connect-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "frame-ancestors 'none';"
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
