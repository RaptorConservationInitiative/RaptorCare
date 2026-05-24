#!/bin/bash

# RaptorCare Installation Script
# Installs all required packages, PostgreSQL, virtualenv, and initializes the database.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"
EXAMPLE_ENV="$REPO_ROOT/.env.example"
VENV_DIR="$REPO_ROOT/venv"
PYTHON_BIN="python3.12"

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

echo_step "Adding deadsnakes PPA for Python 3.12..."
apt-get install -y software-properties-common
add-apt-repository ppa:deadsnakes/ppa -y

echo_step "Updating system packages..."
apt-get update

echo_step "Installing base packages..."
apt-get install -y python3.12 python3.12-venv python3.12-dev git curl wget postgresql libpq-dev nodejs npm

cd "$REPO_ROOT"

echo_step "Preparing Python virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
    $PYTHON_BIN -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

echo_step "Ensuring pip availability (ensurepip + fallback)..."

if ! python -m pip --version >/dev/null 2>&1; then
    $PYTHON_BIN -m ensurepip --upgrade || true
fi

if ! python -m pip --version >/dev/null 2>&1; then
    curl -sS https://bootstrap.pypa.io/get-pip.py | $PYTHON_BIN
fi

echo_step "Upgrading pip tooling..."
python -m pip install --upgrade pip setuptools wheel

# =========================
# 🔥 CUDA TORCH INSTALLATION (IMPORTANT)
# =========================
echo_step "Installing PyTorch with CUDA 11.8 support..."

python -m pip install \
  torch==2.2.2+cu118 torchvision==0.17.2+cu118 torchaudio==2.2.2+cu118 \
  --index-url https://download.pytorch.org/whl/cu118

echo "✅ PyTorch CUDA installed"

# =========================
# REQUIREMENTS INSTALL
# =========================
echo_step "Installing Python dependencies..."
python -m pip install -r "$REPO_ROOT/requirements.txt"

# -------------------------
# DATABASE
# -------------------------
echo_step "PostgreSQL setup"
systemctl enable postgresql --now

sudo -u postgres psql <<SQL
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'raptorcare') THEN
        CREATE ROLE raptorcare LOGIN PASSWORD 'raptorcare_password';
    END IF;
END$$;

CREATE DATABASE raptorcare_db OWNER raptorcare;
SQL

# -------------------------
# ENV
# -------------------------
echo_step ".env setup"
if [ ! -f "$ENV_FILE" ]; then
    cp "$EXAMPLE_ENV" "$ENV_FILE"
fi

# -------------------------
# DB INIT (CRITICAL MISSING PART)
# -------------------------
echo_step "Database schema init"
if [ -f "$REPO_ROOT/scripts/init_db.sh" ]; then
    bash "$REPO_ROOT/scripts/init_db.sh"
else
    echo "⚠️ init_db.sh missing"
fi

# -------------------------
# OLLAMA
# -------------------------
echo_step "Ollama"
if ! command -v ollama >/dev/null 2>&1; then
    curl -fsSL https://ollama.ai/install.sh | sh
fi

# -------------------------
# SYSTEM USER
# -------------------------
echo_step "User"
id -u raptorcare >/dev/null 2>&1 || \
useradd --system --no-create-home --shell /usr/sbin/nologin raptorcare

chown -R raptorcare:raptorcare "$REPO_ROOT"

# -------------------------
# SYSTEMD
# -------------------------
echo_step "systemd service"

cat > /etc/systemd/system/raptorcare.service <<EOF
[Unit]
Description=RaptorCare Server
After=network.target postgresql.service

[Service]
User=raptorcare
WorkingDirectory=$REPO_ROOT
Environment="PATH=$VENV_DIR/bin"
ExecStart=$VENV_DIR/bin/uvicorn server.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now raptorcare.service

# -------------------------
# FINAL CHECK
# -------------------------
echo_step "Healthcheck"

sleep 3
curl -s http://localhost:8000/health || echo "⚠️ API not ready yet"

echo ""
echo "✅ INSTALL COMPLETE"