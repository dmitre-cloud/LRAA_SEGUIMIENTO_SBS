# Dockerfile actualizado para usar Python 3.12 y Alpine
FROM python:3.12-alpine

# Formato preferido para variables de entorno simples (opcional, pero buena práctica)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Instalar dependencias necesarias

WORKDIR /app

RUN apk add --no-cache \
    bash \
    git \
    build-base \
    libffi-dev \
    mysql-dev \
    musl-dev \
    gcc \
    python3-dev \
    py3-pip 

# Copia el archivo requirements.txt y instala las dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código de la aplicación al directorio de trabajo
COPY . .

# Ejecuta collectstatic. Ahora debería encontrar todas las variables de entorno.
RUN python manage.py collectstatic --noinput

# Expone el puerto por defecto de Django
EXPOSE 8058

# Comando para iniciar la aplicación Gunicorn
CMD ["gunicorn", "lraa_project.wsgi:application", "--bind", "0.0.0.0:8058", "--workers", "3"]