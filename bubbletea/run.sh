#!/bin/bash
# Octofree Monitor Launcher
# Quick script to build and run the Bubbletea TUI monitor

cd "$(dirname "$0")"

echo "🔨 Building Octofree Monitor..."
go build -o octofree-monitor main.go

if [ $? -eq 0 ]; then
    echo "✅ Build successful! Starting monitor..."
    echo ""
    ./octofree-monitor
else
    echo "❌ Build failed!"
    exit 1
fi
