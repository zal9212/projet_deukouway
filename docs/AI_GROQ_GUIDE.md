# 🤖 Guide du Module IA & Groq LLM — DEKOUWAY

## 1. Vue d'ensemble
Le module IA (`apps/ai/`) fournit les fonctionnalités conversationnelles, la recommandation intelligente, la modération automatique de contenu et la génération de descriptions immobilières en utilisant exclusivement **Groq API** (`llama-3.3-70b-versatile`).

---

## 2. Sécurité PII & Anonymisation (`AISanitizer`)
Avant tout envoi de prompt à l'API distante, le composant `AISanitizer` anonymise :
- Adresses email -> `[EMAIL_MASQUE]`
- Numéros de téléphone -> `[TELEPHONE_MASQUE]`
- Numéros de carte bancaire -> `[CARTE_MASQUEE]`
- UUIDs sensibles -> `[ID_ANONYMISE]`

---

## 3. Fallback Local & Résilience
En cas de dépassement de délai (timeout > 10.0s) ou d'absence de clé API, le système bascule de manière transparente sur un moteur de règles algorithmique local sans interrompre l'utilisateur.
