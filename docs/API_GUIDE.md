# 🌐 Guide des APIs REST & Documentation Swagger — DEKOUWAY

## 1. Documentation Dynamique
- **Swagger UI** : `http://localhost:8000/api/v1/schema/swagger-ui/`
- **ReDoc** : `http://localhost:8000/api/v1/schema/redoc/`
- **Schéma OpenAPI 3.0 Raw** : `http://localhost:8000/api/v1/schema/`

---

## 2. Authentification Bearer JWT
Toutes les routes privées nécessitent l'en-tête HTTP :
```http
Authorization: Bearer <access_token>
```

### Endpoints d'Authentification (`/api/v1/accounts/`)
- `POST /api/v1/accounts/token/` : Obtenir un jeton Access & Refresh token.
- `POST /api/v1/accounts/token/refresh/` : Renouveler un jeton Access.
- `POST /api/v1/accounts/auth/logout/` : Déconnexion avec révocation immédiate (Token Blacklist).
