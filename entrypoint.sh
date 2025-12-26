#!/bin/bash
set -e

echo "--- STARTING BUNK3R IA INFRASTRUCTURE ---"

# Iniciar Ollama en segundo plano y redirigir logs a la consola de Render
ollama serve 2>&1 | stdbuf -oL tr '\r' '\n' &

echo "Waiting for Ollama to wake up..."
# Esperar a que Ollama esté listo (máximo 60 segundos)
for i in {1..30}; do
  if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "Ollama is awake and ready!"
    break
  fi
  echo "Still waiting for Ollama... ($i/30)"
  sleep 2
done

# Descargar modelo ligero (Cerebro) con progreso visible
echo "Starting model download: llama3.2:1b..."
# Forzar a que la salida de Ollama sea visible en Render
ollama pull llama3.2:1b 2>&1 | stdbuf -oL tr '\r' '\n'

echo "--- MODEL READY, STARTING WEB SERVER ---"

# Iniciar la aplicación Flask con Gunicorn en el puerto que Render espera
PORT=${PORT:-5000}
exec gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 "BUNK3R_IA.main:create_app()"
