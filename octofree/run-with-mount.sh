#!/bin/bash

# Docker run script with volume mount for development/testing
# This mounts the local output directory for persistent data

echo "🚀 Starting octofree container with volume mount..."

# Load environment variables from settings.env
if [ ! -f settings.env ]; then
    echo "❌ Error: settings.env not found!"
    echo "Please create settings.env from settings.env.template"
    exit 1
fi

# Get the current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Stop and remove any existing test container
if docker ps -a | grep -q octofree-test; then
    echo "🧹 Cleaning up existing octofree-test container..."
    docker stop octofree-test 2>/dev/null
    docker rm octofree-test 2>/dev/null
fi

# Run the container in detached mode with volume mount
echo "🐳 Starting container with volume mount..."
docker run -d \
    --name octofree-test \
    --env-file settings.env \
    -v "${SCRIPT_DIR}/output:/app/output" \
    octofree

# Check if container started successfully
if [ $? -eq 0 ]; then
    echo "✅ Container started successfully!"
    echo ""
    echo "Container name: octofree-test"
    echo "Status: Running with volume mount"
    echo "Output directory: ${SCRIPT_DIR}/output"
    echo ""
    echo "Useful commands:"
    echo "  View logs:        docker logs -f octofree-test"
    echo "  Check local files: ls -la ${SCRIPT_DIR}/output"
    echo "  Stop container:   docker stop octofree-test"
    echo "  Remove container: docker rm octofree-test"
    echo ""
    echo "📋 Showing last 10 log lines..."
    sleep 2
    docker logs --tail 10 octofree-test
else
    echo "❌ Failed to start container"
    exit 1
fi
