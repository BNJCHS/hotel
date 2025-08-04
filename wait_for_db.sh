#!/bin/sh

echo "Esperando a que la base de datos esté disponible en $DB_HOST:$DB_PORT..."

# Esperar hasta que la DB esté disponible
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 1
done

echo "Base de datos disponible. Iniciando servidor Django..."

exec "$@"
