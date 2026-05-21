#!/bin/bash
# RaptorCare Station Client Installation Script
# Offline-first client for rescue station

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_DIR="/opt/raptorcare-station"
STATION_SERVICE_FILE="/etc/systemd/system/raptorcare-station.service"
PYTHON_BIN="python3"

function echo_step() {
    echo -e "\n🔧 $1"
}

if [[ $EUID -ne 0 ]]; then
    echo "❌ Please run as root: sudo bash scripts/install_station.sh"
    exit 1
fi

echo "🦅 RaptorCare Station Client Installation"
echo "========================================="

echo_step "Updating system packages..."
apt-get update
apt-get install -y python3 python3-venv python3-dev git curl wget

echo_step "Preparing station repository..."
if [[ -f "$REPO_ROOT/station/app.py" ]]; then
    echo "✅ Using local repository at $REPO_ROOT"
    STATION_DIR="$REPO_ROOT"
else
    echo "📁 Creating station installation directory at $TARGET_DIR"
    mkdir -p "$TARGET_DIR"
    if [[ ! -d "$TARGET_DIR/.git" ]]; then
        git clone https://github.com/RaptorConservationInitiative/RaptorCare.git "$TARGET_DIR"
    fi
    STATION_DIR="$TARGET_DIR"
fi

echo_step "Creating station system user..."
if ! id -u raptorcare-station >/dev/null 2>&1; then
    useradd --system --no-create-home --shell /usr/sbin/nologin raptorcare-station
    echo "✅ Created user raptorcare-station"
else
    echo "✅ User raptorcare-station already exists"
fi

echo_step "Creating Python virtual environment..."
if [[ ! -d "$STATION_DIR/venv" ]]; then
    $PYTHON_BIN -m venv "$STATION_DIR/venv"
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

source "$STATION_DIR/venv/bin/activate"
python3 -m pip install --upgrade pip setuptools wheel

echo_step "Installing Python dependencies..."
if [[ -f "$STATION_DIR/requirements.txt" ]]; then
    python3 -m pip install -r "$STATION_DIR/requirements.txt"
else
    echo "⚠️  requirements.txt not found in $STATION_DIR"
fi

echo_step "Installing station systemd service..."
cat > "$STATION_SERVICE_FILE" <<EOF
[Unit]
Description=RaptorCare Station FastAPI Server
After=network.target

[Service]
Type=simple
User=raptorcare-station
WorkingDirectory=$STATION_DIR
Environment="PATH=$STATION_DIR/venv/bin"
ExecStart=$STATION_DIR/venv/bin/uvicorn station.app:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

chmod 644 "$STATION_SERVICE_FILE"
systemctl daemon-reload
systemctl enable raptorcare-station.service

cat <<EOF

✅ Station installation complete!

Usage:
  systemctl start raptorcare-station.service
  systemctl status raptorcare-station.service

If you want to start it immediately:
  systemctl start raptorcare-station.service

Station app path:
  $STATION_DIR/station/app.py

EOF
