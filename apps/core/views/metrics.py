from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter, Histogram

# Métriques personnalisées Prometheus
REQUEST_COUNT = Counter('dekouway_http_requests_total', 'Total des requêtes HTTP', ['method', 'endpoint'])
RESPONSE_LATENCY = Histogram('dekouway_http_response_latency_seconds', 'Latence des réponses HTTP', ['endpoint'])

def metrics_view(request):
    """
    Endpoint d'exportation des métriques Prometheus (/metrics/).
    Protégé par un jeton partagé (METRICS_TOKEN) : ces métriques (taux de requêtes,
    latences par endpoint) ne doivent être lisibles que par le collecteur Prometheus
    interne, pas par n'importe quel visiteur du site.
    """
    expected_token = getattr(settings, 'METRICS_TOKEN', '')
    provided_token = request.headers.get('X-Metrics-Token', '')
    if not expected_token or provided_token != expected_token:
        return HttpResponseForbidden("Accès refusé.")

    metrics_data = generate_latest()
    return HttpResponse(metrics_data, content_type=CONTENT_TYPE_LATEST)
