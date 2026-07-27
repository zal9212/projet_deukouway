#!/bin/bash
# Script de sauvegarde automatique PostgreSQL DEKOUWAY

BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
FILENAME="dekouway_backup_${TIMESTAMP}.sql.gz"

mkdir -p ${BACKUP_DIR}

echo "Début de la sauvegarde PostgreSQL DEKOUWAY..."
docker exec -t dekouway_db pg_dump -U dekouway_user dekouway_db | gzip > ${BACKUP_DIR}/${FILENAME}

echo "Sauvegarde terminée avec succès : ${BACKUP_DIR}/${FILENAME}"
