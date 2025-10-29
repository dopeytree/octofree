#!/bin/sh
# Octofree Docker Console Entry Script
# This script runs when you attach to the Docker console

echo "╔════════════════════════════════════════════════════╗"
echo "║         OCTOFREE ENERGY MONITOR                    ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""
echo "Python app is running in the background..."
echo ""
echo "Options:"
echo "  [1] Launch TUI Monitor (interactive dashboard)"
echo "  [2] View logs (tail -f)"
echo "  [3] Shell access"
echo "  [q] Exit console"
echo ""
echo -n "Choose an option: "

read choice

case $choice in
    1)
        echo "Launching TUI Monitor..."
        /usr/local/bin/octofree-monitor
        ;;
    2)
        echo "Viewing logs (Ctrl+C to exit)..."
        tail -f /data/octofree.log
        ;;
    3)
        echo "Starting shell..."
        /bin/sh
        ;;
    *)
        echo "Exiting..."
        ;;
esac
