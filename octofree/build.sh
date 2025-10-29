#!/bin/bash

# Build the Docker image with Go TUI included
echo "Building Docker image with TUI monitor..."
docker build -t octofree .

echo "Build complete!"
echo ""
echo "To run the container:"
echo "  docker run -d --name octofree -v \$(pwd)/output:/data octofree"
echo ""
echo "To launch the TUI monitor:"
echo "  docker exec -it octofree octofree-monitor"
echo ""
echo "To view logs:"
echo "  docker exec -it octofree tail -f /data/octofree.log"
echo ""

# Optional: Run vulnerability scan using Trivy (commented out for speed)
# Uncomment if you want to scan
# echo "Running vulnerability scan with Trivy..."
# docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy image octofree

echo "Build complete."