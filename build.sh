#!/bin/bash

# Build the Docker image
echo "Building Docker image..."
docker build -t octofree .

# Run vulnerability scan using Trivy
echo "Running vulnerability scan with Trivy..."
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy image octofree

echo "Build and scan complete."