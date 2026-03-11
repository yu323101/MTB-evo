#!/bin/bash
# Download VarScan if not exists

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VARSCAN_JAR="$SCRIPT_DIR/VarScan.v2.3.9.jar"
VARSCAN_URL="https://sourceforge.net/projects/varscan/files/VarScan.v2.3.9.jar"

echo "=== VarScan Download Script ==="
echo ""

if [ -f "$VARSCAN_JAR" ]; then
    echo "✓ VarScan already exists: $VARSCAN_JAR"
    exit 0
fi

echo "Downloading VarScan v2.3.9..."
echo "Source: $VARSCAN_URL"
echo "Destination: $VARSCAN_JAR"
echo ""

if command -v wget > /dev/null 2>&1; then
    wget -O "$VARSCAN_JAR" "$VARSCAN_URL" --show-progress
elif command -v curl > /dev/null 2>&1; then
    curl -L -o "$VARSCAN_JAR" "$VARSCAN_URL" --progress-bar
else
    echo "Error: Neither wget nor curl found. Please install one of them."
    exit 1
fi

if [ -f "$VARSCAN_JAR" ]; then
    echo ""
    echo "✓ VarScan downloaded successfully!"
    echo "Location: $VARSCAN_JAR"
else
    echo ""
    echo "✗ Error: Failed to download VarScan"
    exit 1
fi
