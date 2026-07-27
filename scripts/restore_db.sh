#!/bin/bash
# Script de restauration PostgreSQL DEKOUWAY

if [ -z "$1" ]; then
    echo "Usage: ./scripts/restore_db.sh <chemin_du_fichier_backup.sql.gz>"
    exit 1
fi

BACKUP_FILE=$1

echo "Restauration de la base de données depuis ${BACKUP_FILE}..."
gunzip -c ${BACKUP_FILE} | docker exec -i dekouway_db psql -U dekouway_user -d dekouway_db

echo "Restauration terminée avec succès !"
