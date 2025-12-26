FROM python:3.11-slim

# Instalar dependencias necesarias
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copiar el proyecto
WORKDIR /app
COPY . .

# Instalar dependencias de Python
RUN pip3 install --no-cache-dir -r requirements.txt

# Script de inicio
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 10000

ENTRYPOINT ["/entrypoint.sh"]
