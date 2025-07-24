FROM python:3.11-slim

WORKDIR /code

# Instalar dependencias del sistema necesarias para compilar mysqlclient
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    && apt-get clean
RUN apt-get update && apt-get install -y netcat-openbsd


COPY requirements.txt /code/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . /code/
COPY wait_for_db.sh /wait_for_db.sh
RUN chmod +x /wait_for_db.sh

ENTRYPOINT ["/wait_for_db.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
