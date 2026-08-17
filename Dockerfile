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

# /app lui-même appartient encore à root (créé par WORKDIR avant ce point) :
# sans ce chown, appuser ne peut pas y créer staticfiles/ ou media/ au runtime.
RUN mkdir -p staticfiles media && chown -R appuser:appgroup /app && chmod +x entrypoint.sh

# Dropping privileges to non-root user
USER appuser

EXPOSE 8000

# collectstatic + migrations au démarrage (pas au build : SECRET_KEY/DATABASE_URL
# n'existent qu'au runtime sur les plateformes PaaS comme Render, jamais pendant
# `docker build` — les lancer ici au lieu d'un `RUN` évite un manifest statique
# vide ou périmé silencieusement généré par un collectstatic qui a échoué au build).
CMD ["./entrypoint.sh"]
