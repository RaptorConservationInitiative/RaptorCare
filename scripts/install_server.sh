#!/bin/bash

# RaptorCare Installation Script for Proxmox LXC
# Installs all dependencies and services

set -e

echo "🦅 RaptorCare Installation"
echo "===================================="

# Update system
echo "📦 Updating system packages..."
apt-get update
apt-get install -y python3.11 python3-pip python3-venv git curl wget

# Create installation directory
if [ ! -d "/opt/raptorcare" ]; then
    echo "📁 Creating /opt/raptorcare..."
    mkdir -p /opt/raptorcare
    cd /opt/raptorcare
else
    cd /opt/raptorcare
fi

# Clone repository (if not already done)
if [ ! -d ".git" ]; then
    echo "📥 Cloning RaptorCare repository..."
    git clone https://github.com/RaptorConservationInitiative/RaptorCare.git .
fi

# Create Python virtual environment
if [ ! -d "venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3.11 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip setuptools wheel
    pip install -r requirements.txt
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Install PostgreSQL client (for connection)
echo "🐘 Installing PostgreSQL client..."
apt-get install -y postgresql-client libpq-dev

# Install NVIDIA GPU utilities (if NVIDIA GPU present)
if command -v nvidia-smi &> /dev/null; then
    echo "🎮 NVIDIA GPU detected"
    echo "✅ CUDA support available"
else
    echo "⚠️  No NVIDIA GPU detected - ensure nvidia-docker is installed"
fi

# Install Ollama
echo "🤖 Installing Ollama..."
if command -v ollama &> /dev/null; then
    echo "✅ Ollama already installed"
else
    curl https://ollama.ai/install.sh | sh
    echo "✅ Ollama installed"
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your configuration:"
    echo "   nano .env"
fi

echo ""
echo "✨ Installation Complete!"
echo ""
echo "🚀 Next Steps:"
echo "   1. Edit .env configuration:"
echo "      nano .env"
echo ""
echo "   2. Setup systemd services:"
echo "      sudo bash scripts/setup_systemd.sh"
echo ""
echo "   3. Start services:"
echo "      sudo systemctl start raptorcare"
echo "      sudo systemctl start ollama"
echo ""
echo "   4. Check status:"
echo "      sudo systemctl status raptorcare"
echo "      journalctl -u raptorcare -f"
echo ""
