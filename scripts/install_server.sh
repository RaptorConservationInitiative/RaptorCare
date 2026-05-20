#!/bin/bash
# Server installation script for Proxmox LXC

set -e

echo "🦅 RaptorCare Server Installer"
echo "================================"

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
    postgresql \
    postgresql-contrib \
    git \
    curl \
    wget \
    supervisor

# Create venv
echo "🐍 Creating Python virtual environment..."
python3 -m venv /opt/raptorcare/venv
source /opt/raptorcare/venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python packages..."
pip install --upgrade pip setuptools wheel
pip install -r /opt/raptorcare/requirements.txt

# Setup PostgreSQL
echo "🗄️  Setting up PostgreSQL..."
sudo -u postgres psql <<EOF
CREATE USER raptorcare WITH PASSWORD 'raptorcare_password';
CREATE DATABASE raptorcare_db OWNER raptorcare;
GRANT ALL PRIVILEGES ON DATABASE raptorcare_db TO raptorcare;
EOF

# Setup supervisor
echo "⚙️  Setting up supervisor..."
cat > /etc/supervisor/conf.d/raptorcare.conf << 'EOF'
[program:raptorcare-server]
command=/opt/raptorcare/venv/bin/python -m uvicorn server.main:app --host 0.0.0.0 --port 8000
directory=/opt/raptorcare
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/raptorcare/server.err.log
stdout_logfile=/var/log/raptorcare/server.out.log
EOF

mkdir -p /var/log/raptorcare
chown www-data:www-data /var/log/raptorcare

echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "1. Configure .env file:"
echo "   cp .env.example .env"
echo "   nano .env"
echo ""
echo "2. Initialize database:"
echo "   source /opt/raptorcare/venv/bin/activate"
echo "   python -c 'from server.database import init_db; init_db()'"
echo ""
echo "3. Start services:"
echo "   supervisorctl reread"
echo "   supervisorctl update"
echo "   supervisorctl start raptorcare-server"
