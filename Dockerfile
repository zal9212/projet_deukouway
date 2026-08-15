# Stage 1: Build & Dependencies
FROM python:3.12-slim as builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Production Runtime (Non-root Hardened)
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Hardening Security: Création d'un utilisateur non-privilégié appuser
RUN groupadd -g 10001 appgroup && \
    useradd -u 10000 -g appgroup -s /bin/sh -m appuser

COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH

COPY --chown=appuser:appgroup . .

# Collectstatic
RUN python manage.py collectstatic --noinput || true

RUN chmod +x entrypoint.sh

# Dropping privileges to non-root user
USER appuser

EXPOSE 8000

# Migrations au démarrage (nécessitent la base, injoignable au build) puis gunicorn.
CMD ["./entrypoint.sh"]
