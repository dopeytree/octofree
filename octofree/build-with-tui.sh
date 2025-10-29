#!/bin/bash
# Build script that handles the multi-directory structure

echo "🐙 Building Octofree Docker Image with TUI Monitor..."
echo ""

# Change to parent directory to include both octofree and bubbletea in build context
cd "$(dirname "$0")/.."

echo "Building from: $(pwd)"
echo ""

# Build with parent directory as context, using octofree/Dockerfile
docker build -f octofree/Dockerfile.multi -t octofree .

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Build complete!"
    echo ""
    echo "To run the container:"
    echo "  docker run -d --name octofree -v \$(pwd)/octofree/output:/data octofree"
    echo ""
    echo "To launch the TUI monitor:"
    echo "  docker exec -it octofree octofree-monitor"
    echo ""
    echo "Or use the quick launcher:"
    echo "  ./octofree/tui-launcher.sh"
else
    echo ""
    echo "❌ Build failed!"
    exit 1
fi
