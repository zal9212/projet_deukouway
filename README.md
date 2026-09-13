# KYI IMMOBILIER

Plateforme SaaS de location immobilière au Sénégal (Django 5.2 + PostgreSQL), avec un tableau de bord dédié pour les voyageurs, les propriétaires et le SuperAdmin, un assistant IA (Groq), et un flux complet d'inscription/vérification KYC des propriétaires.

## Démarrage rapide (développement local)

```bash
cp .env.example .env
# Éditez .env : définissez DATABASE_URL en pointant vers votre PostgreSQL local
# (ou laissez tel quel si vous utilisez docker-compose, voir plus bas)

python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### CSS (Tailwind)

Le CSS est compilé localement (plus de CDN Tailwind en production). Après toute modification d'un template, régénérez le fichier compilé :

```bash
npm install
npm run build:css      # build unique et minifié
npm run watch:css      # rebuild automatique pendant le développement
```

Le fichier généré `static/css/tailwind.css` est commité : un déploiement n'a donc pas besoin de Node.js pour fonctionner, seulement pour re-générer ce fichier après un changement de template.

## Démarrage avec Docker

```bash
cp .env.example .env
docker-compose up --build
```

Voir [docs/DOCKER_DEPLOYMENT.md](docs/DOCKER_DEPLOYMENT.md) pour le détail du déploiement en production.

## Documentation

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — architecture générale (services/selectors, apps Django)
- [docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) — guide développeur
- [docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md) — schéma de base de données
- [docs/API_GUIDE.md](docs/API_GUIDE.md) — API REST
- [docs/AI_GROQ_GUIDE.md](docs/AI_GROQ_GUIDE.md) — assistant IA (Groq)
- [docs/ADMIN_GUIDE.md](docs/ADMIN_GUIDE.md) — guide SuperAdmin
- [docs/USER_GUIDE_CLIENT.md](docs/USER_GUIDE_CLIENT.md) / [docs/USER_GUIDE_OWNER.md](docs/USER_GUIDE_OWNER.md) — guides utilisateurs

## Tests

```bash
python manage.py test
```
