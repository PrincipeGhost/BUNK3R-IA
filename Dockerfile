# Base image with Python
FROM python:3.9-slim-buster

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Code-Server
RUN curl -fsSL https://code-server.dev/install.sh | sh

# Install Node.js (for runtime if needed by extensions)
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && apt-get install -y nodejs

# Set work directory
WORKDIR /app

# Copy python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Copy Application Code
COPY . .

# Install BUNK3R Extension
# Ensure the .vsix is present in vscode-extension/ folder
RUN code-server --install-extension vscode-extension/bunk3r-ai-extension-0.1.0.vsix

# Environment Setup
ENV PORT=10000
# Code-Server specific envs to allow access
ENV PASSWORD=bunk3r_secure_access
ENV BIND_ADDR=0.0.0.0:10000

# Copy Entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose Render Port
EXPOSE 10000

# Start
ENTRYPOINT ["/entrypoint.sh"]
