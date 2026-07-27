# 🏛️ Documentation Architecturale — DEKOUWAY

## 1. Principes Directeurs
La plateforme **DEKOUWAY** est développée en suivant une architecture **Clean Architecture + Domain Driven Design (DDD) + Modular Monolith**.

### Regroupement en Couches :
- **Couche Domaine (`models.py`, `choices.py`, `exceptions.py`)** : Définition des entités, règles immuables et exceptions métier.
- **Couche Métier (`services/services.py`)** : Reçoit les requêtes d'écriture, exécute les règles métier et applique les mutations sous `@transaction.atomic`.
- **Couche Lecture (`services/selectors.py`)** : Optimise la récupération de données en prévenant les requêtes N+1 via `select_related` et `prefetch_related`.
- **Couche Présentation & REST API (`forms.py`, `api/serializers.py`, `api/viewsets.py`)** : Vues fines (Thin Views) sans logique métier, déléguant l'exécution aux services.

---

## 2. Monolithe Modulaire (Modules Applicatifs)
```
apps/
├── core/            # Modèle de base, Mixins, Middleware, Emails, Health & Metrics
├── accounts/        # Authentification, Profils, KYC, Adresses, Sessions
├── properties/      # Logements, Catégories, Équipements, Validation
├── reservations/    # Demandes de réservation, Workflow, Réservations fermes
├── payments/        # Transactions (Wave/OM/Carte), Commissions (15%), Reversements
├── notifications/   # Notifications système & Préférences
├── documents/       # Gestion des pièces justificatives & Contrats
├── support/         # Tickets de support & Gestion des litiges
├── dashboard/       # Agrégats et KPIs Client, Propriétaire, SuperAdmin
├── analytics/       # Mesures et statistiques
└── ai/              # Module d'Intelligence Artificielle Groq
```
