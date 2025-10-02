FROM python:3.13-alpine

# Auto-patch vulnerabilities in base image
RUN apk update && apk upgrade --no-cache

WORKDIR /app

# Install system packages if your script needs them (e.g., for curl or git)
RUN apk add --no-cache curl

# Copy requirements first for better caching (if you have one)
COPY requirements.txt .
# Upgrade pip to patch vulnerabilities
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy your script(s) and template
COPY . .

# Set up configuration from template if no settings.env exists
RUN if [ ! -f settings.env ]; then cp settings.env.template settings.env; fi

# Environment variables can be passed during docker run
ENV DISCORD_WEBHOOK_URL=""
ENV SINGLE_RUN="false"
ENV TEST_MODE="false"

# Run your main script
CMD ["python3", "octofree.py"]