#!/bin/bash

# RaptorCare Installation Script
# Installs all required packages, PostgreSQL, virtualenv, and initializes the database.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"
EXAMPLE_ENV="$REPO_ROOT/.env.example"
VENV_DIR="$REPO_ROOT/venv"
PYTHON_BIN="python3"

function echo_step() {
    echo -e "\n🔧 $1"
}

function ensure_package() {
    local pkg="$1"
    if ! dpkg -s "$pkg" >/dev/null 2>&1; then
        apt-get install -y "$pkg"
    fi
}

if [[ $EUID -ne 0 ]]; then
    echo "❌ Please run this script as root: sudo bash scripts/install_server.sh"
    exit 1
fi

echo "🦅 RaptorCare Installation"
echo "===================================="

echo_step "Updating system packages..."
apt-get update

# Base packages
echo_step "Installing base packages..."
apt-get install -y python3 python3-pip python3-venv python3-dev git curl wget postgresql postgresql-contrib libpq-dev nodejs npm

# Create or use current repository path
cd "$REPO_ROOT"

echo_step "Preparing Python virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
    $PYTHON_BIN -m venv "$VENV_DIR"
    echo "✅ Virtual environment created at $VENV_DIR"
else
    echo "✅ Virtual environment already exists at $VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
python3 -m pip install --upgrade pip setuptools wheel
python3 -m pip install -r "$REPO_ROOT/requirements.txt"

echo_step "Installing and building UI packages..."
if [ -d "$REPO_ROOT/server_ui" ]; then
  cd "$REPO_ROOT/server_ui"
  npm install
  npm run build
  echo "✅ Built server UI"
fi
if [ -d "$REPO_ROOT/station_ui" ]; then
  cd "$REPO_ROOT/station_ui"
  npm install
  npm run build
  echo "✅ Built station UI"
fi
cd "$REPO_ROOT"

# PostgreSQL setup
echo_step "Ensuring PostgreSQL service is running..."
systemctl enable postgresql --now

echo_step "Creating PostgreSQL role and database..."
RUN_PSQL="sudo -u postgres psql -v ON_ERROR_STOP=1"
$RUN_PSQL <<'SQL'
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'raptorcare') THEN
        CREATE ROLE raptorcare LOGIN PASSWORD 'raptorcare_password';
    ELSE
        ALTER ROLE raptorcare WITH PASSWORD 'raptorcare_password';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'raptorcare_db') THEN
        CREATE DATABASE raptorcare_db OWNER raptorcare;
    END IF;
END$$;
SQL

echo_step "Creating .env file if missing..."
if [ ! -f "$ENV_FILE" ]; then
    cp "$EXAMPLE_ENV" "$ENV_FILE"
    echo "✅ Created $ENV_FILE"
else
    echo "✅ Existing $ENV_FILE retained"
fi

echo_step "Initializing database schema and admin user..."
bash "$REPO_ROOT/scripts/init_db.sh"

echo_step "Installing Ollama LLM..."
if command -v ollama >/dev/null 2>&1; then
    echo "✅ Ollama already installed"
else
    curl -fsSL https://ollama.ai/install.sh | sh
    echo "✅ Ollama installed"
fi

OLLAMA_BIN="$(command -v ollama || true)"

echo_step "Creating system user and systemd service for RaptorCare..."
if ! id -u raptorcare >/dev/null 2>&1; then
    useradd --system --no-create-home --shell /usr/sbin/nologin raptorcare
    echo "✅ Created user raptorcare"
else
    echo "✅ User raptorcare already exists"
fi

chown -R raptorcare:raptorcare "$REPO_ROOT"

cat > /etc/systemd/system/raptorcare.service <<EOF
[Unit]
Description=RaptorCare FastAPI Server
After=network.target postgresql.service

[Service]
Type=notify
User=raptorcare
WorkingDirectory=$REPO_ROOT
Environment="PATH=$VENV_DIR/bin"
Environment="PYTHONUNBUFFERED=1"
ExecStart=$VENV_DIR/bin/uvicorn server.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

chmod 644 /etc/systemd/system/raptorcare.service
systemctl daemon-reload
systemctl enable --now raptorcare.service

echo "✅ Started raptorcare.service"

if [[ -n "$OLLAMA_BIN" ]]; then
    echo_step "Creating system user and systemd service for Ollama..."
    if ! id -u ollama >/dev/null 2>&1; then
        useradd --system --no-create-home --shell /usr/sbin/nologin ollama
        echo "✅ Created user ollama"
    else
        echo "✅ User ollama already exists"
    fi

    mkdir -p /var/lib/ollama/models
    chown -R ollama:ollama /var/lib/ollama || true

    cat > /etc/systemd/system/ollama.service <<EOF
[Unit]
Description=Ollama LLM Server
After=network.target

[Service]
Type=simple
User=ollama
Environment="PATH=$PATH"
ExecStart=$OLLAMA_BIN serve
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ollama

[Install]
WantedBy=multi-user.target
EOF

    chmod 644 /etc/systemd/system/ollama.service
    systemctl daemon-reload
    systemctl enable --now ollama.service
    echo "✅ Started ollama.service"
fi

cat <<EOF

✨ Installation Complete!

The central server is running as a systemd service:
  systemctl status raptorcare.service

EOF
if [[ -n "$OLLAMA_BIN" ]]; then
cat <<EOF
The Ollama service is running as:
  systemctl status ollama.service

EOF
fi

