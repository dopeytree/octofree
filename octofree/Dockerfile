FROM python:3.14-alpine

# Auto-patch vulnerabilities in base image
RUN apk update && apk upgrade --no-cache && \
    # Remove apk cache to reduce image size and attack surface
    rm -rf /var/cache/apk/*

WORKDIR /app

# Install system packages if your script needs them (e.g., for curl or git)
# Pin versions and remove unnecessary packages
RUN apk add --no-cache \
    curl \
    ca-certificates \
    && rm -rf /var/cache/apk/*

# Copy requirements first for better caching (if you have one)
COPY requirements.txt .

# Upgrade pip and setuptools to latest versions to patch known vulnerabilities
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    # Install dependencies with hash checking for security
    pip install --no-cache-dir -r requirements.txt && \
    # Remove pip cache
    rm -rf /root/.cache/pip

# Copy your script(s) and template
COPY . .

# Set up configuration from template if no settings.env exists
RUN if [ ! -f settings.env ]; then cp settings.env.template settings.env; fi

# Create a non-root user for security
RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Environment variables can be passed during docker run
ENV DISCORD_WEBHOOK_URL=""
ENV SINGLE_RUN="false"
ENV TEST_MODE="false"

# Run your main script
CMD ["python3", "main.py"]