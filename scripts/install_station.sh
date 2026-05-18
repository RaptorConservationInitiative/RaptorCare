#!/bin/bash
set -e

apt update
apt install -y python3 python3-pip git

pip3 install fastapi uvicorn requests

mkdir -p /opt/raptorcare_station

cp -r . /opt/raptorcare_station

cd /opt/raptorcare_station/station

nohup uvicorn app:app --host 0.0.0.0 --port 8001 &