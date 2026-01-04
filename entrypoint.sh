#!/bin/bash
set -e

echo "--- STARTING BUNK3R IA INFRASTRUCTURE ---"

echo "--- STARTING WEB SERVER ---"

# Iniciar la aplicación Flask con Gunicorn en el puerto que Render espera
PORT=${PORT:-5000}
exec gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 "backend.main:create_app()"
