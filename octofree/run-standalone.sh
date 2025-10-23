#!/bin/bash

# Docker run script for self-contained testing
# This creates a standalone container without volume mounts

echo "🚀 Starting self-contained octofree container..."

# Load environment variables from settings.env
if [ ! -f settings.env ]; then
    echo "❌ Error: settings.env not found!"
    echo "Please create settings.env from settings.env.template"
    exit 1
fi

# Source the settings.env file
set -a
source settings.env
set +a

# Stop and remove any existing standalone container
if docker ps -a | grep -q octofree-standalone; then
    echo "🧹 Cleaning up existing octofree-standalone container..."
    docker stop octofree-standalone 2>/dev/null
    docker rm octofree-standalone 2>/dev/null
fi

# Run the container in detached mode with all environment variables
echo "🐳 Starting container..."
docker run -d \
    --name octofree-standalone \
    -e DISCORD_WEBHOOK_URL="${DISCORD_WEBHOOK_URL}" \
    -e BEARER_TOKEN="${BEARER_TOKEN}" \
    -e TEST_MODE="${TEST_MODE:-false}" \
    -e SINGLE_RUN="${SINGLE_RUN:-false}" \
    -e TEST_X_SCRAPER="${TEST_X_SCRAPER:-false}" \
    -e OUTPUT_DIR="/data" \
    octofree

# Check if container started successfully
if [ $? -eq 0 ]; then
    echo "✅ Container started successfully!"
    echo ""
    echo "Container name: octofree-standalone"
    echo "Status: Running as self-contained unit (no volume mounts)"
    echo ""
    echo "Useful commands:"
    echo "  View logs:        docker logs -f octofree-standalone"
    echo "  Check files:      docker exec octofree-standalone ls -la /data"
    echo "  Stop container:   docker stop octofree-standalone"
    echo "  Remove container: docker rm octofree-standalone"
    echo ""
    echo "📋 Showing last 10 log lines..."
    sleep 2
    docker logs --tail 10 octofree-standalone
else
    echo "❌ Failed to start container"
    exit 1
fi
