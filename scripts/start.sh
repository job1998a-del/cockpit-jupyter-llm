#!/bin/bash
# Start script for the Dual Assistant

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Activate venv if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Activated virtual environment"
fi

# Check for config
if [ ! -f "config/config.yaml" ]; then
    echo "⚠️  config/config.yaml not found"
    echo "   Copying from config.example.yaml..."
    cp config/config.example.yaml config/config.yaml
    echo "   Edit config/config.yaml to add your API credentials"
fi

# Run the dual assistant
echo "🚀 Starting Dual Assistant..."
python -m assistants.dual_assistant
