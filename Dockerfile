FROM python:3.12-alpine

# Auto-patch vulnerabilities in base image
RUN apk update && apk upgrade --no-cache

WORKDIR /app

# Install system packages if your script needs them (e.g., for curl or git)
RUN apk add --no-cache curl

# Copy requirements first for better caching (if you have one)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Upgrade pip to patch vulnerabilities
RUN pip install --upgrade pip

# Copy your script(s)
COPY . .

# Run your main script
CMD ["python3", "octofree.py"]