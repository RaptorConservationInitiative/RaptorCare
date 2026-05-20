#!/bin/bash

# RaptorCare Server Systemd Setup Script
# Configures FastAPI and Ollama as systemd services for auto-startup

set -e

echo "🦅 RaptorCare Systemd Service Setup"
echo "===================================="

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root (use sudo)"
   exit 1
fi

# Create raptorcare user if it doesn't exist
if ! id -u raptorcare > /dev/null 2>&1; then
    echo "👤 Creating raptorcare system user..."
    useradd --system --no-create-home --shell /bin/false raptorcare
    echo "✅ User created"
fi

# Create ollama user if it doesn't exist
if ! id -u ollama > /dev/null 2>&1; then
    echo "👤 Creating ollama system user..."
    useradd --system --no-create-home --shell /bin/false ollama
    echo "✅ User created"
fi

# Copy FastAPI service file
echo "📋 Installing RaptorCare FastAPI service..."
cp raptorcare.service /etc/systemd/system/raptorcare.service
chmod 644 /etc/systemd/system/raptorcare.service
echo "✅ FastAPI service installed"

# Copy Ollama service file
echo "📋 Installing Ollama LLM service with dual GPU..."
cp ollama.service /etc/systemd/system/ollama.service
chmod 644 /etc/systemd/system/ollama.service
echo "✅ Ollama service installed"

# Set correct permissions for raptorcare directory
echo "🔒 Setting permissions..."
chown -R raptorcare:raptorcare /opt/raptorcare
chmod 750 /opt/raptorcare
echo "✅ Permissions set"

# Reload systemd daemon
echo "🔄 Reloading systemd daemon..."
systemctl daemon-reload
echo "✅ Systemd reloaded"

# Enable services for auto-start
echo "🚀 Enabling auto-startup..."
systemctl enable raptorcare.service
systemctl enable ollama.service
echo "✅ Services enabled for auto-startup"

echo ""
echo "✨ Setup Complete!"
echo ""
echo "📌 Next steps:"
echo "   1. Configure .env file:"
echo "      nano /opt/raptorcare/.env"
echo ""
echo "   2. Start services:"
echo "      sudo systemctl start raptorcare"
echo "      sudo systemctl start ollama"
echo ""
echo "   3. Check status:"
echo "      sudo systemctl status raptorcare"
echo "      sudo systemctl status ollama"
echo ""
echo "   4. View logs:"
echo "      sudo journalctl -u raptorcare -f"
echo "      sudo journalctl -u ollama -f"
echo ""
echo "   5. GPU Status:"
echo "      nvidia-smi"
echo ""
