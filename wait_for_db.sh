#!/bin/sh
set -e

host="${DB_HOST:-db}"
port="${DB_PORT:-3306}"

echo "Esperando a la base de datos en $host:$port..."
until nc -z "$host" "$port"; do
  sleep 2
done

echo "Base de datos disponible, iniciando Django..."
exec "$@"
