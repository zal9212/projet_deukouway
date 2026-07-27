import multiprocessing

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gthread"
threads = 2
timeout = 60
keepalive = 5

accesslog = "-"
errorlog = "-"
loglevel = "info"

max_requests = 1000
max_requests_jitter = 50
