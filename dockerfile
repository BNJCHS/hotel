FROM python:3.11-slim

WORKDIR /code

# Instalar herramientas necesarias
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    netcat-openbsd \
    && apt-get clean

# Copiar e instalar dependencias
COPY requirements.txt /code/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copiar todo el código al contenedor
COPY . /code/

# Copiar el script y darle permisos
COPY wait_for_db.sh /wait_for_db.sh
RUN chmod +x /wait_for_db.sh

# Punto de entrada: espera a la DB
ENTRYPOINT ["/wait_for_db.sh"]

# Comando por defecto: correr el servidor Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
