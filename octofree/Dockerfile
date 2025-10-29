# Stage 1: Build Go TUI
FROM golang:1.23-alpine AS go-builder

WORKDIR /build

# Copy Go module files
COPY bubbletea/go.mod bubbletea/go.sum ./
RUN go mod download

# Copy Go source
COPY bubbletea/ ./
RUN go build -o octofree-monitor .

# Stage 2: Final Python runtime image
FROM python:3.14-alpine

# Auto-patch vulnerabilities in base image
RUN apk update && apk upgrade --no-cache && \
    rm -rf /var/cache/apk/*

WORKDIR /app

# Install system packages
RUN apk add --no-cache \
    curl \
    ca-certificates \
    && rm -rf /var/cache/apk/*

# Copy requirements first for better caching
COPY requirements.txt .

# Upgrade pip and install dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    rm -rf /root/.cache/pip

# Copy Python application
COPY . .

# Copy Go TUI binary from builder stage
COPY --from=go-builder /build/octofree-monitor /usr/local/bin/octofree-monitor
RUN chmod +x /usr/local/bin/octofree-monitor

# Copy and setup console script
COPY docker-console.sh /usr/local/bin/docker-console
RUN chmod +x /usr/local/bin/docker-console

# Set up configuration from template if no settings.env exists
RUN if [ ! -f settings.env ]; then cp settings.env.template settings.env; fi

# Create /data directory for volume mounting with full permissions
RUN mkdir -p /data && chmod 777 /data

# Declare volume for persistent data
VOLUME ["/data"]

# Environment variables
ENV DISCORD_WEBHOOK_URL=""
ENV SINGLE_RUN="false"
ENV TEST_MODE="false"
ENV OUTPUT_DIR="/data"

# Create a simple launcher script that allows choosing between Python app and TUI
RUN echo '#!/bin/sh' > /usr/local/bin/launcher && \
    echo 'if [ "$1" = "monitor" ]; then' >> /usr/local/bin/launcher && \
    echo '  exec /usr/local/bin/octofree-monitor' >> /usr/local/bin/launcher && \
    echo 'else' >> /usr/local/bin/launcher && \
    echo '  exec python3 /app/main.py "$@"' >> /usr/local/bin/launcher && \
    echo 'fi' >> /usr/local/bin/launcher && \
    chmod +x /usr/local/bin/launcher

# Default: Run Python main script
WORKDIR /app
CMD ["python3", "/app/main.py"]
