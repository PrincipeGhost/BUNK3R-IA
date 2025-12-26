#!/bin/bash

# Iniciar Ollama en segundo plano
ollama serve &

# Esperar a que Ollama esté listo
for i in {1..30}; do
  if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "Ollama is ready!"
    break
  fi
  echo "Waiting for Ollama..."
  sleep 2
done

# Descargar modelo ligero (Cerebro)
ollama pull llama3.2:1b

# Iniciar la aplicación Flask con Gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 2 --threads 4 "BUNK3R_IA.main:create_app()"
