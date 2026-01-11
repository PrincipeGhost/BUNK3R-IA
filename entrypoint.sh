#!/bin/bash

# Ensure PORT is set (Render default)
export PORT=${PORT:-10000}
export PYTHONPATH=$PYTHONPATH:/opt/bunk3r-ia

echo "BUNK3R-IA: Preparing environment..."

# 1. Configure Nginx with the dynamic PORT (Only replace $PORT)
envsubst '$PORT' < /opt/bunk3r-ia/nginx.conf.template > /etc/nginx/nginx.conf

# 2. Start Python Backend (Singularity)
echo "Starting BUNK3R Python Backend (Port 5000)..."
cd /opt/bunk3r-ia
gunicorn --bind 127.0.0.1:5000 --workers 2 --threads 4 'backend.main:app' &

# 3. Start Code-Server (VS Code IDE)
echo "Starting Code-Server (Port 8080)..."
# Create default settings to open BUNK3R chat by default
mkdir -p /opt/code-server-data/User
echo '{"workbench.auxiliaryBar.visible": true, "workbench.view.extension.chat": true}' > /opt/code-server-data/User/settings.json

PORT="" code-server \
    --bind-addr 127.0.0.1:8080 \
    --auth none \
    --disable-telemetry \
    --disable-extension vscode.chat \
    --disable-extension vscode.interactive \
    --user-data-dir /opt/code-server-data \
    /workspace &

# 4. Start Nginx Proxy as the foreground process
echo "BUNK3R-IA is LIVE on Port $PORT"
nginx -g 'daemon off;'
