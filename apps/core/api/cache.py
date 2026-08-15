from django.core.cache import cache
from functools import wraps
from rest_framework.response import Response
import logging

logger = logging.getLogger(__name__)

def cache_response(timeout: int = 300, key_prefix: str = ''):
    """
    Décorateur réutilisable pour mettre en cache les réponses d'API en lecture seule.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            if request.method != 'GET':
                return func(self, request, *args, **kwargs)
                
            cache_key = f"{key_prefix}:{request.get_full_path()}"
            if request.user and request.user.is_authenticated:
                cache_key += f":user_{request.user.id}"

            cached_data = cache.get(cache_key)
            if cached_data is not None:
                logger.debug(f"Cache HIT for key: {cache_key}")
                return Response(cached_data)

            response = func(self, request, *args, **kwargs)
            if response.status_code == 200 and hasattr(response, 'data'):
                cache.set(cache_key, response.data, timeout=timeout)
                logger.debug(f"Cache SET for key: {cache_key}")
            return response
        return wrapper
    return decorator


def invalidate_cache_pattern(pattern: str):
    """
    Invalide toutes les clés de cache correspondant à un préfixe donné.
    """
    try:
        if hasattr(cache, 'delete_pattern'):
            cache.delete_pattern(f"*{pattern}*")
        else:
            cache.clear()
        logger.info(f"Cache invalidé pour le motif : {pattern}")
    except Exception as e:
        logger.warning(f"Impossible d'invalider le cache pour {pattern}: {e}")
