#!/bin/bash
set -e

apt update
apt install -y python3 python3-pip git postgresql redis-server

pip install --break-system-packages -r requirements.txt

mkdir -p /opt/raptorcare

cp -r . /opt/raptorcare

cd /opt/raptorcare/server

nohup uvicorn main:app --host 0.0.0.0 --port 8000 &