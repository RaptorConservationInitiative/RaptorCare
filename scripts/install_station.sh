#!/bin/bash
# RaptorCare Station Client Installation Script
# Offline-first client for rescue station

set -e

echo "🦅 RaptorCare Station Client Installation"
echo "========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}[1/3] Updating system packages...${NC}"
apt-get update
apt-get install -y python3 python3-venv python3-dev git

echo -e "${YELLOW}[2/3] Creating Python virtual environment...${NC}"
python3 -m venv /opt/raptorcare-station/venv
/opt/raptorcare-station/venv/bin/pip install --upgrade pip setuptools wheel

echo -e "${YELLOW}[3/3] Installing Python dependencies...${NC}"
if [ -f requirements.txt ]; then
    /opt/raptorcare-station/venv/bin/pip install -r requirements.txt
fi

echo ""
echo -e "${GREEN}✅ Station Client installed!${NC}"
echo ""
echo "Usage:"
echo "  /opt/raptorcare-station/venv/bin/python station/client.py"
echo ""
