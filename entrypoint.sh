#!/bin/sh
# Exécuté à chaque démarrage du conteneur, pas au build : collectstatic et les
# migrations ont besoin des variables d'environnement (SECRET_KEY, DATABASE_URL)
# et/ou de la base de données, qui ne sont disponibles qu'au runtime sur les
# plateformes PaaS comme Render — jamais pendant `docker build`.
set -e

python manage.py collectstatic --noinput
python manage.py migrate --noinput

exec gunicorn --config gunicorn.conf.py dekouway.wsgi:application
