#!/bin/bash
# RaptorCare Station Client Installation Script
# Offline-first client for rescue station

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_DIR="/opt/raptorcare-station"
STATION_SERVICE_FILE="/etc/systemd/system/raptorcare-station.service"
PYTHON_BIN="python3.12"

function echo_step() {
    echo -e "\n🔧 $1"
}

if [[ $EUID -ne 0 ]]; then
    echo "❌ Please run as root: sudo bash scripts/install_station.sh"
    exit 1
fi

echo "🦅 RaptorCare Station Client Installation"
echo "========================================="

echo_step "Adding deadsnakes PPA for Python 3.12..."
apt-get update
apt-get install -y software-properties-common
add-apt-repository ppa:deadsnakes/ppa -y

echo_step "Updating system packages..."
apt-get update
apt-get install -y python3.12 python3.12-venv python3.12-dev git curl wget nodejs npm

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
if ! python3.12 -m pip --version >/dev/null 2>&1; then
    echo_step "Bootstrapping pip for Python 3.12..."
    curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12
fi
python3.12 -m pip install --upgrade pip setuptools wheel

echo_step "Installing Python dependencies..."
if [[ -f "$STATION_DIR/requirements.txt" ]]; then
    python3.12 -m pip install -r "$STATION_DIR/requirements.txt"
else
    echo "⚠️  requirements.txt not found in $STATION_DIR"
fi

echo_step "Installing station UI dependencies and building UI..."
if [[ -d "$STATION_DIR/station_ui" ]]; then
    cd "$STATION_DIR/station_ui"
    npm install
    npm run build
    echo "✅ Built station UI"
    cd "$STATION_DIR"
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
systemctl enable --now raptorcare-station.service
chown -R raptorcare-station:raptorcare-station "$STATION_DIR"

cat <<EOF

✅ Station installation complete!

The station service is running as a systemd service:
  systemctl status raptorcare-station.service

Station app path:
  $STATION_DIR/station/app.py

EOF
