# 💻 Guide Développeur & Contribution — DEKOUWAY

## 1. Setup Local & Lancement de la Suite de Tests
```bash
# 1. Cloner et préparer l'environnement virtuel
python -m venv .venv
source .venv/bin/activate  # ou .\.venv\Scripts\Activate.ps1 sous Windows

# 2. Installer toutes les dépendances
pip install -r requirements.txt

# 3. Lancer les migrations de base de données
python manage.py migrate

# 4. Exécuter la suite complète des tests (Unitaires, API, IA)
python manage.py test apps.accounts.tests apps.properties.tests apps.reservations.tests apps.payments.tests apps.notifications.tests apps.documents.tests apps.support.tests apps.dashboard.tests apps.ai.tests
```

## 2. Commandes d'Outillage (Load & E2E Tests)
- **Tests de Charge Locust** :
  ```bash
  locust -f tests/load/locustfile.py --headless -u 10 -r 2 --run-time 10s
  ```
- **Tests E2E Playwright** :
  ```bash
  npx playwright test
  ```
