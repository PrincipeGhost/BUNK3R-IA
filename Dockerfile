# Base image with Python
FROM python:3.9-slim-bullseye

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    nginx \
    gettext-base \
    && rm -rf /var/lib/apt/lists/*

# Install Code-Server
RUN curl -fsSL https://code-server.dev/install.sh | sh

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && apt-get install -y nodejs

# Create protected app directory and public workspace
RUN mkdir -p /opt/bunk3r-ia /workspace && chmod 777 /workspace

# Set work directory to the protected app area
WORKDIR /opt/bunk3r-ia

# Copy python requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Copy Application Code
COPY . .

# Install BUNK3R Extension in a central location
RUN code-server --user-data-dir /opt/code-server-data --install-extension vscode-extension/bunk3r-ai-extension-0.1.0.vsix

# Environment Setup
ENV PASSWORD=bunk3r_secure_access
ENV BUNK3R_INTERNAL_PATH=/opt/bunk3r-ia
ENV WORKSPACE_DIR=/workspace

# Copy Entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose Render Port (Nginx Proxy)
EXPOSE 10000

# Start
ENTRYPOINT ["/entrypoint.sh"]
