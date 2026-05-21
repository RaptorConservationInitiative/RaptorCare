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
apt-get install -y python3 python3-pip python3-venv python3-dev git curl wget postgresql postgresql-contrib libpq-dev

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

echo_step "Optional: Installing Ollama LLM..."
if command -v ollama >/dev/null 2>&1; then
    echo "✅ Ollama already installed"
else
    curl -fsSL https://ollama.ai/install.sh | sh
    echo "✅ Ollama installed"
fi

cat <<EOF

✨ Installation Complete!

Next steps:
  1. Edit .env if needed:
       nano "$ENV_FILE"
  2. Start the central server:
       source "$VENV_DIR/bin/activate"
       uvicorn server.main:app --reload
  3. Optional: Start Ollama:
       ollama serve

If you want auto-start services, run:
  sudo bash scripts/setup_systemd.sh

EOF
