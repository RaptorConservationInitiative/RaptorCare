#!/bin/bash
# Station installation script (Client-side)

set -e

echo "🦅 RaptorCare Station Client Installer"
echo "======================================="

# Update system
echo "📦 Updating system packages..."
apt-get update
apt-get upgrade -y

# Install system dependencies
echo "📦 Installing system dependencies..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    sqlite3 \
    node.js \
    npm \
    git \
    curl

# Create venv
echo "🐍 Creating Python virtual environment..."
python3 -m venv /opt/raptorcare-station/venv
source /opt/raptorcare-station/venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python packages..."
pip install --upgrade pip setuptools wheel
pip install -r /opt/raptorcare-station/requirements.txt

# Setup frontend
echo "📱 Setting up React frontend..."
cd /opt/raptorcare-station/frontend
npm install
npm run build

echo "✅ Station installation complete!"
echo ""
echo "Next steps:"
echo "1. Configure station connection:"
echo "   export REACT_APP_API_URL=http://server-ip:8000"
echo ""
echo "2. Start the application:"
echo "   cd /opt/raptorcare-station"
echo "   npm start"
