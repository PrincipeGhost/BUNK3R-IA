#!/bin/bash

# Start Python Backend in background
echo "Starting BUNK3R Python Backend on port 5000..."
gunicorn --bind 0.0.0.0:5000 --workers 2 --threads 4 'backend.main:app' &

# Wait for backend to be ready (simple sleep for now)
sleep 5

# Start Code-Server in foreground (this keeps container alive)
# BIND_ADDR env var handles the port 10000 binding for Render
echo "Starting Code-Server on port $PORT..."
code-server --bind-addr 0.0.0.0:$PORT --auth password --disable-telemetry .
