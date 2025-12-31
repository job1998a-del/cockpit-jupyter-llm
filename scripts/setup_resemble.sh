#!/bin/bash

# Trinity Core - Resemble.AI Setup Script
echo "🚀 Setting up Trinity Core with Resemble.AI..."

# Install dependencies for voice manipulation
echo "📦 Installing system packages..."
sudo apt update && sudo apt install -y ffmpeg libsndfile1

# Create directories
echo "📁 Creating persistence directories..."
mkdir -p memory_db vector_store models logs ssl

# Copy secrets template if it doesn't exist
if [ ! -f "config/secrets.yaml" ]; then
    echo "⚙️  Initializing config/secrets.yaml..."
    cp config/secrets.example.yaml config/secrets.yaml
    echo "📝 Please edit config/secrets.yaml with your API keys"
fi

echo "✅ Local setup complete!"
echo "🐳 Next step: Run 'docker-compose up -d' to start the stack."
