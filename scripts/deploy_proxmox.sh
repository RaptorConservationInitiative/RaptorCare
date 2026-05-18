#!/bin/bash
set -e

TEMPLATE="local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst"

pct create 300 $TEMPLATE \
  --hostname raptorcore \
  --cores 8 \
  --memory 16384 \
  --rootfs ssdpool:64 \
  --net0 name=eth0,bridge=vmbr0,ip=dhcp \
  --features nesting=1 \
  --unprivileged 0

pct start 300