#!/bin/bash

# RaptorCare Installation Script (FIXED FULL VERSION)
# Installs all required packages, PostgreSQL, virtualenv, and initializes the database.
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

set -euo pipefail

PYTHON_BIN="python3.12"

TARGET_DIR="/opt/raptorcare"
VENV_DIR="$TARGET_DIR/venv"
ENV_FILE="$TARGET_DIR/.env"
EXAMPLE_ENV="$TARGET_DIR/.env.example"

UPLOAD_DIR="/var/lib/raptorcare/uploads"

OLLAMA_BIN=""

echo "🦅 RaptorCare Installation (Production Mode)"
echo "===================================="


function echo_step() {
    echo -e "\n🔧 $1"
}

# -------------------------
# ROOT CHECK
# -------------------------
if [[ $EUID -ne 0 ]]; then
    echo "❌ Run as root: sudo bash install.sh"
    exit 1
fi

# -------------------------
# SYSTEM USER
# -------------------------
useradd --system --no-create-home --shell /usr/sbin/nologin raptorcare 2>/dev/null || true

# -------------------------
# SYSTEM USER
# -------------------------
echo_step "Creating system user..."

if ! id -u raptorcare >/dev/null 2>&1; then
    useradd --system --no-create-home --shell /usr/sbin/nologin raptorcare
fi

# -------------------------
# UPLOAD DIR
# -------------------------
echo "📁 Creating upload directory..."
mkdir -p "$UPLOAD_DIR"
chown -R raptorcare:raptorcare /var/lib/raptorcare
chmod -R 750 /var/lib/raptorcare

# -------------------------
# DEPENDENCIES
# -------------------------
echo "📦 Installing dependencies..."
apt-get update
apt-get install -y \
    python3.12 python3.12-venv python3.12-dev \
    postgresql libpq-dev \
    nodejs npm software-properties-common \
    git curl wget rsync

# -------------------------
# PROJECT DEPLOY
# -------------------------
echo_step "Deploying project to /opt/raptorcare..."
mkdir -p "$TARGET_DIR"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
rsync -a --delete --exclude venv --exclude .git "$REPO_ROOT/" "$TARGET_DIR/"
REPO_ROOT="$TARGET_DIR"

cd "$TARGET_DIR"

chown -R raptorcare:raptorcare "$TARGET_DIR"

# -------------------------
# VENV
# -------------------------
echo "🐍 Setting up venv..."
if [ ! -d "$VENV_DIR" ]; then
    $PYTHON_BIN -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
echo_step "Ensuring pip availability..."

if ! python -m pip --version >/dev/null 2>&1; then
    $PYTHON_BIN -m ensurepip --upgrade || true
fi

if ! python -m pip --version >/dev/null 2>&1; then
    curl -sS https://bootstrap.pypa.io/get-pip.py | $PYTHON_BIN
fi

echo_step "Upgrading pip tooling..."
python -m pip install --upgrade pip setuptools wheel

# -------------------------
# PYTORCH
# -------------------------
echo "🔥 Installing PyTorch..."
pip install torch==2.2.2+cu118 torchvision==0.17.2+cu118 torchaudio==2.2.2+cu118 \
 --index-url https://download.pytorch.org/whl/cu118

echo "✅ PyTorch installed"

# -------------------------
# REQUIREMENTS
# -------------------------
echo_step "Installing Python dependencies..."
python -m pip install -r "$REPO_ROOT/requirements.txt"
# -------------------------
# POSTGRES
# -------------------------
echo "🗄️ Starting PostgreSQL..."
systemctl enable postgresql --now

sudo -u postgres psql <<'SQL'
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'raptorcare') THEN
        CREATE ROLE raptorcare LOGIN PASSWORD 'raptorcare_password';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'raptorcare_db') THEN
        CREATE DATABASE raptorcare_db OWNER raptorcare;
    END IF;
END$$;
SQL

# -------------------------
# DB INIT
# -------------------------
echo_step "Initializing database..."
bash "$REPO_ROOT/scripts/init_db.sh"

# -------------------------
# ENV FILE
# -------------------------
if [ ! -f "$ENV_FILE" ]; then
    cp "$EXAMPLE_ENV" "$ENV_FILE"
fi

# -------------------------
# UI BUILD (FIXED)
# -------------------------
echo "🖥️ Building UI..."

if [ -d "$TARGET_DIR/server_ui" ]; then
    cd "$TARGET_DIR/server_ui"
    npm install
    npm run build
    mkdir -p "$TARGET_DIR/server/static_ui"
    cp -r dist/* "$TARGET_DIR/server/static_ui/"
fi

# -------------------------
# OLLAMA INSTALL (FIX RESTORED)
# -------------------------
echo "🤖 Installing Ollama..."

if ! command -v ollama >/dev/null 2>&1; then
    curl -fsSL https://ollama.ai/install.sh | sh
fi

OLLAMA_BIN="$(command -v ollama || true)"

# -------------------------
# OLLAMA SYSTEMD SERVICE
# -------------------------
if [[ -n "$OLLAMA_BIN" ]]; then

    echo "⚙️ Installing Ollama service..."

    useradd --system --no-create-home --shell /usr/sbin/nologin ollama 2>/dev/null || true

    mkdir -p /var/lib/ollama/models
    chown -R ollama:ollama /var/lib/ollama || true

    cat > /etc/systemd/system/ollama.service <<EOF
[Unit]
Description=Ollama LLM Server
After=network.target

[Service]
Type=simple
User=ollama
ExecStart=$OLLAMA_BIN serve
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable ollama.service
    systemctl start ollama.service
fi

# -------------------------
# SYSTEMD APP SERVICE (FIXED)
# -------------------------
echo "⚙️ Installing RaptorCare service..."

cat > /etc/systemd/system/raptorcare.service <<EOF
[Unit]
Description=RaptorCare Server
After=network.target postgresql.service ollama.service

[Service]
Type=simple
User=raptorcare
WorkingDirectory=$TARGET_DIR
Environment="PYTHONUNBUFFERED=1"

ExecStart=$VENV_DIR/bin/uvicorn server.main:app \
  --host 0.0.0.0 \
  --port 8000

Restart=on-failure
RestartSec=5
TimeoutStartSec=300

ReadWritePaths=/var/lib/raptorcare

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable raptorcare.service

echo "🚀 Starting RaptorCare..."

if ! systemctl start raptorcare.service; then
    echo "❌ Service failed:"
    systemctl status raptorcare.service --no-pager || true
    journalctl -xeu raptorcare.service --no-pager || true
    exit 1
fi

# -------------------------
# DONE
# -------------------------
echo ""
echo "✅ INSTALLATION COMPLETE"
echo "========================"
echo "Backend: http://localhost:8000"
echo "API:     http://localhost:8000/docs"
echo "UI:      http://localhost:8000/ui (if mounted)"
echo "Ollama:  systemctl status ollama.service"
echo ""

# -------------------------
# FINAL CHECK
# -------------------------
echo_step "Healthcheck"

sleep 3
curl -s http://localhost:8000/health || echo "⚠️ API not ready yet"

echo ""
echo "✅ INSTALL COMPLETE"