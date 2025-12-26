FROM ollama/ollama:latest

# Instalar Python y dependencias necesarias
RUN apt-get update && apt-get install -y python3 python3-pip curl

# Copiar el proyecto
WORKDIR /app
COPY . .

# Instalar dependencias de Python
RUN pip3 install --no-cache-dir -r requirements.txt

# Script de inicio para arrancar Ollama y la App
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 5000

ENTRYPOINT ["/entrypoint.sh"]
