#!/bin/sh

# Espera a que la base de datos esté disponible antes de arrancar Django
echo "Esperando a que la base de datos esté disponible en $DB_HOST:$DB_PORT..."

# Intentar conexión hasta que funcione
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 1
done

echo "Base de datos disponible. Iniciando servidor Django..."

# Ejecutar el comando que sigue (por ejemplo, runserver)
exec "$@"
