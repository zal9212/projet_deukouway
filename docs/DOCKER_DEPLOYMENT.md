# 🐳 Guide de Déploiement Docker & Nginx — DEKOUWAY

## 1. Démarrage Rapide sous Docker Compose
```bash
# 1. Copier le fichier d'environnement
cp .env.example .env

# 2. Lancer la stack complète
docker-compose up --build -d

# 3. Vérifier les conteneurs actifs
docker-compose ps
```

---

## 2. Architecture de la Stack Déploiement
- `web` : Conteneur Python 3.12 exécutant Gunicorn (`gunicorn.conf.py`) sur le port 8000.
- `db` : Conteneur PostgreSQL 16 avec volume persistant `postgres_data`.
- `redis` : Conteneur Redis 7 pour le cache d'application et la limitation de débit.
- `nginx` : Reverse proxy gérant le SSL, la compression Gzip et le service des fichiers statiques/médias via WhiteNoise.
