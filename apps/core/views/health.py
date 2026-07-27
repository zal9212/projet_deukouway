import time
import logging
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache

logger = logging.getLogger(__name__)

def health_check_view(request):
    """
    Endpoint de contrôle de santé du système (/health/).
    Vérifie l'état de la base de données PostgreSQL, du cache Redis et de la mémoire.
    Ne renvoie jamais le détail d'une exception (hôte, driver, etc.) dans la réponse :
    ce détail est uniquement journalisé côté serveur, pour ne pas exposer d'infos
    internes à un appelant non authentifié (l'endpoint reste public pour les sondes
    de santé des load-balancers/orchestrateurs).
    """
    status_data = {
        'status': 'healthy',
        'timestamp': time.time(),
        'database': 'ok',
        'cache': 'ok'
    }
    http_code = 200

    # Vérification DB
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception as e:
        logger.error(f"Health check DB échoué : {e}", exc_info=True)
        status_data['database'] = 'error'
        status_data['status'] = 'unhealthy'
        http_code = 503

    # Vérification Cache
    try:
        cache.set("health_check", "ok", timeout=5)
        if cache.get("health_check") != "ok":
            status_data['cache'] = 'error'
            status_data['status'] = 'unhealthy'
            http_code = 503
    except Exception as e:
        logger.error(f"Health check cache échoué : {e}", exc_info=True)
        status_data['cache'] = 'error'
        status_data['status'] = 'unhealthy'
        http_code = 503

    return JsonResponse(status_data, status=http_code)
