#!/bin/bash

# Ensure PORT is set (default to 10000 for local testing)
export PORT=${PORT:-10000}

echo "Configuring Nginx with PORT $PORT..."
# Replace $PORT in template and save to /etc/nginx/nginx.conf
envsubst '${PORT}' < /app/nginx.conf.template > /etc/nginx/nginx.conf

# Start Python Backend (Singularity AI)
echo "Starting BUNK3R Python Backend (Port 5000)..."
gunicorn --bind 127.0.0.1:5000 --workers 2 --threads 4 'backend.main:app' &

# Start Code-Server (VS Code IDE)
echo "Starting Code-Server (Port 8080)..."
code-server --bind-addr 127.0.0.1:8080 --auth password --disable-telemetry . &

# Start Nginx as the main process (Port $PORT)
echo "Starting Nginx Proxy (Port $PORT)..."
nginx -g 'daemon off;'
