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
# We serve from /workspace. Logged in users will be redirected to /workspace/user_id
echo "Starting Code-Server (Port 8080)..."
# We use a shared user-data-dir where the extension was installed during build
PORT="" code-server \
    --bind-addr 127.0.0.1:8080 \
    --auth none \
    --disable-telemetry \
    --user-data-dir /opt/code-server-data \
    /workspace &

# 4. Start Nginx Proxy as the foreground process
echo "BUNK3R-IA is LIVE on Port $PORT"
nginx -g 'daemon off;'
