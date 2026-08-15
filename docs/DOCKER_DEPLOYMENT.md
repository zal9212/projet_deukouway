# 🐳 Guide de Déploiement Docker & Nginx — DEKOUWAY

## 1. Démarrage Rapide sous Docker Compose
```bash
# 1. Copier le fichier d'environnement
cp .env.example .env
# Puis éditer .env : voir section 3 "Checklist .env de production" ci-dessous.

# 2. Lancer la stack complète
docker-compose up --build -d

# 3. Appliquer les migrations et les fichiers statiques
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput

# 4. Vérifier les conteneurs actifs
docker-compose ps
docker-compose logs -f web
```

---

## 2. Architecture de la Stack Déploiement
- `web` : Conteneur Python 3.12 exécutant Gunicorn (`gunicorn.conf.py`) sur le port 8000.
- `db` : Conteneur PostgreSQL 16 avec volume persistant `postgres_data` (pas de port exposé sur l'hôte : joignable uniquement par `web`).
- `redis` : Conteneur Redis 7 pour le cache d'application et la limitation de débit (idem, pas de port exposé).
- `nginx` : Reverse proxy gérant la compression Gzip et le service des fichiers statiques/médias. **Ne gère pas encore le SSL par défaut** (voir section 4) : `nginx.conf` n'écoute que le port 80 tant que le certificat n'est pas installé.

---

## 3. Checklist `.env` de production (obligatoire avant le premier lancement)

| Variable | Valeur |
|---|---|
| `DEBUG` | `False` |
| `SECRET_KEY` | Une clé unique et secrète (`python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`) — **jamais** celle de `.env.example` |
| `ALLOWED_HOSTS` | Le(s) domaine(s) et/ou IP réel(s) du serveur, ex: `dekouway.sn,www.dekouway.sn` |
| `CSRF_TRUSTED_ORIGINS` | `https://dekouway.sn,https://www.dekouway.sn` (ou `http://` si HTTPS pas encore actif, voir section 4) |
| `POSTGRES_PASSWORD` | Un mot de passe fort et unique — **jamais** `securepassword123` |
| `DATABASE_URL` | Doit reprendre exactement le même mot de passe que `POSTGRES_PASSWORD` |
| `METRICS_TOKEN` | Un jeton aléatoire si `/metrics/` doit être exposé à Prometheus, sinon laisser vide |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Laisser vides/commentés pour garder la connexion Google désactivée (déjà le cas actuellement) |
| `GROQ_API_KEY` | Optionnel : sans clé, l'assistant IA bascule automatiquement sur ses réponses de secours locales, sans erreur |

⚠️ Ne jamais commiter le `.env` réel (déjà dans `.gitignore`).

---

## 4. Activer HTTPS (Let's Encrypt / Certbot)

**Le premier déploiement se fait volontairement en HTTP simple** (`SECURE_SSL_REDIRECT=False` dans `.env`) : obtenir un certificat Let's Encrypt exige que le domaine pointe déjà (DNS propagé) vers l'IP du serveur, ce qui n'est pas toujours possible dès la première mise en ligne.

Une fois le DNS du domaine pointé vers le serveur et le site accessible en HTTP :

```bash
# 1. Installer certbot sur l'hôte (pas dans le conteneur)
sudo apt-get update && sudo apt-get install -y certbot

# 2. Obtenir le certificat (le conteneur nginx doit tourner et servir /.well-known/ sur le port 80)
sudo certbot certonly --webroot -w /chemin/vers/static -d dekouway.sn -d www.dekouway.sn

# 3. Ajouter un bloc "server { listen 443 ssl; ... }" dans nginx.conf pointant vers les
#    certificats générés (/etc/letsencrypt/live/dekouway.sn/), monter ce dossier en volume
#    dans le service nginx du docker-compose.yml, puis redémarrer :
docker-compose restart nginx

# 4. Une fois HTTPS confirmé fonctionnel, repasser SECURE_SSL_REDIRECT=True dans .env
# et redémarrer web : docker-compose restart web
```

---

## 5. Déploiement gratuit sur Oracle Cloud (Always Free)

Oracle Cloud offre une vraie VM **gratuite à vie** (pas un essai limité) avec disque persistant — la seule option gratuite qui fonctionne avec ce projet **sans changement de code**, puisque les documents (pièces d'identité, photos de logements) sont stockés sur disque local et non dans un stockage cloud.

### 5.1 Créer le compte et la VM
1. Créer un compte sur [cloud.oracle.com](https://cloud.oracle.com) (carte bancaire demandée pour vérification, jamais débitée sur l'offre Always Free). **La "Home Region" choisie à l'inscription est définitive** : préférer une région proche (ex. Europe) pour la latence.
2. Menu ☰ → **Compute → Instances → Create Instance**.
3. **Image** : Ubuntu 22.04 (ou plus récent).
4. **Shape** : cliquer *Change shape* → *Ampere* → `VM.Standard.A1.Flex` → régler **2 OCPU / 12 GB RAM** (large marge sous l'allocation gratuite de 4 OCPU / 24 GB — Postgres + Redis + Django + Nginx ensemble ont besoin de plus que le micro-instance AMD à 1 GB).
5. **Networking** : garder la VCN par défaut, cocher *Assign a public IPv4 address*.
6. **SSH keys** : laisser Oracle générer une paire de clés et **télécharger la clé privée** (`ssh-key-*.key`) — impossible à retélécharger ensuite.
7. *Create*. Noter l'**adresse IP publique** une fois la VM active.

### 5.2 Ouvrir les ports (le piège classique Oracle)
Oracle filtre le trafic **à deux niveaux** ; il faut ouvrir les deux, sinon le site reste injoignable même une fois déployé :

**a) Security List (niveau réseau, dans la console Oracle)**
Instance → lien de la VCN → *Security Lists* → liste par défaut → *Add Ingress Rules* → ajouter TCP `80` et TCP `443`, source `0.0.0.0/0`.

**b) Pare-feu de la VM elle-même (iptables, à l'intérieur de la VM)**
```bash
ssh -i /chemin/vers/ssh-key-*.key ubuntu@<IP_PUBLIQUE>
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save   # rend la règle permanente au redémarrage
```

### 5.3 Installer Docker
```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg git
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker $USER && newgrp docker
```

### 5.4 Récupérer le code et déployer
```bash
git clone https://github.com/zal9212/projet_deukouway.git
cd projet_deukouway
git checkout develop   # ou la branche à déployer

cp .env.example .env
nano .env   # renseigner les valeurs réelles — voir section 3 ci-dessus
#   ALLOWED_HOSTS=<IP_PUBLIQUE ou domaine>
#   SECURE_SSL_REDIRECT=False   (tant que le HTTPS n'est pas encore actif, section 4)

docker compose up --build -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py collectstatic --noinput
docker compose exec web python manage.py createsuperuser
```
Le site est alors joignable sur `http://<IP_PUBLIQUE>/`.

### 5.5 HTTPS sans nom de domaine payant
Let's Encrypt exige un nom de domaine (pas une IP nue). Pour rester à 0 F :
- [DuckDNS](https://www.duckdns.org) ou [nip.io](https://nip.io) offrent un sous-domaine gratuit pointé vers l'IP publique de la VM.
- Une fois le sous-domaine actif, suivre la section 4 ci-dessus (`certbot`) normalement.

### 5.6 Limite à connaître
Oracle a occasionnellement récupéré des VM Always Free jugées inactives (peu ou pas de trafic pendant plusieurs semaines). Un usage régulier du site suffit à l'éviter ; ce n'est pas garanti contractuellement comme le serait un VPS payant.
