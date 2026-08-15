import multiprocessing
import os

# PORT est injecté par les plateformes PaaS (Render, etc.) ; 8000 reste le défaut
# pour Docker Compose / usage local, où le port est fixé par nous-mêmes.
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
# WEB_CONCURRENCY permet de brider le nombre de workers sur les environnements à
# mémoire limitée (ex. Render free tier) où cpu_count()*2+1 sature le RAM disponible.
workers = int(os.environ.get('WEB_CONCURRENCY', multiprocessing.cpu_count() * 2 + 1))
worker_class = "gthread"
threads = 2
timeout = 60
keepalive = 5

accesslog = "-"
errorlog = "-"
loglevel = "info"

max_requests = 1000
max_requests_jitter = 50
