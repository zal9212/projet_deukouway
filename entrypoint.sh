#!/bin/sh
# Exécuté à chaque démarrage du conteneur (contrairement à collectstatic, qui a
# lieu une fois au build : les migrations ont besoin de la base de données, qui
# n'est joignable qu'au runtime, jamais pendant `docker build`).
set -e

python manage.py migrate --noinput

exec gunicorn --config gunicorn.conf.py dekouway.wsgi:application
