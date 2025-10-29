#!/bin/bash
# Quick launcher for the TUI monitor
# Usage: ./tui-launcher.sh [container-name]

CONTAINER_NAME=${1:-octofree}

echo "🐙 Launching Octofree TUI Monitor..."
echo "Container: $CONTAINER_NAME"
echo ""

# Check if container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "❌ Error: Container '$CONTAINER_NAME' is not running"
    echo ""
    echo "Start it with:"
    echo "  docker run -d --name $CONTAINER_NAME -v \$(pwd)/output:/data octofree"
    exit 1
fi

# Launch the TUI
docker exec -it $CONTAINER_NAME octofree-monitor

echo ""
echo "TUI closed. Python app continues running in background."
