# 🗄️ Schéma de la Base de Données — DEKOUWAY (PostgreSQL 16)

## 1. Identifiants & Audit (`BaseModel`)
Toutes les tables de l'application héritent du modèle de base `BaseModel` (`apps/core/models.py`) :
- `id` : `UUID` (v4, Clé primaire immuable)
- `created_at` : `DateTime` (Horodatage de création)
- `updated_at` : `DateTime` (Horodatage de modification)
- `is_deleted` : `Boolean` (Suppression logique Soft Delete)
- `deleted_at` : `DateTime` (Horodatage de suppression)

---

## 2. Intégrité Référentielle & Protections (`PROTECT`)
- Les modèles financiers et contractuels (`Reservation`, `Payment`, `Payout`, `Commission`) utilisent `on_delete=models.PROTECT` pour empêcher toute suppression accidentelle d'historique comptable.
- Les contraintes de type `CheckConstraint` garantissent la validité des prix (`price > 0`), surfaces (`surface > 0`) et dates (`check_out > check_in`).
