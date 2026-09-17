#!/usr/bin/env bash
# Stop the service, the optical line and the packet topology, in that order.
#
#   sudo scripts/service-down.sh
#
# Each step is attempted even if an earlier one failed, so a partially started
# lab still gets cleaned up. Only this lab's topology is destroyed; a global
# Containerlab or emulator cleanup would take unrelated labs on the host with
# it, so neither is run here.

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PACKET="$ROOT/packet-network"
RUNTIME="${RUNTIME_DIR:-$ROOT/.runtime}"
OPTICAL_PID="$RUNTIME/optical.pid"
VENV="${VENV_PYTHON:-$ROOT/.venv/bin/python}"

step() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

[ "$(id -u)" -eq 0 ] || { echo "run with sudo" >&2; exit 1; }

step "1/3  service"
if [ -x "$VENV" ]; then
    "$VENV" "$PACKET/main.py" traffic stop 2>/dev/null || echo "  (no traffic to stop)"
fi

step "2/3  optical line"
# Ask it to stop so it tears down its own namespaces and detaches cleanly, then
# confirm by the state rather than by the signal's return value: a kill that
# succeeds against a stale pid says nothing about whether the line is gone.
# Releasing port 8080 is the condition that matters, because that is what a
# later start checks.
port_held() { ss -ltn 2>/dev/null | grep -q '127.0.0.1:8080 '; }

if [ -f "$OPTICAL_PID" ]; then
    xargs -r kill -TERM <"$OPTICAL_PID" 2>/dev/null || true
fi
pkill -TERM -f 'main\.py start --attach' 2>/dev/null || true

for _ in $(seq 1 30); do
    port_held || break
    sleep 1
done
if port_held; then
    echo "  did not stop on request; forcing"
    if [ -f "$OPTICAL_PID" ]; then
        xargs -r kill -KILL <"$OPTICAL_PID" 2>/dev/null || true
    fi
    pkill -KILL -f 'main\.py start --attach' 2>/dev/null || true
    for _ in $(seq 1 10); do
        port_held || break
        sleep 1
    done
fi
rm -f "$OPTICAL_PID"

if port_held; then
    echo "  WARNING: something is still serving port 8080; a later start will refuse"
else
    echo "  stopped"
fi

step "3/3  packet topology"
if [ -x "$VENV" ]; then
    "$VENV" "$PACKET/main.py" destroy
else
    containerlab destroy --topo "$PACKET/topology.clab.yml"
fi

cat <<'EOF'

Stopped. If the optical line was killed rather than asked to stop, leftover
emulator namespaces may remain; clear them with:

  sudo optical-network/main.py clean

Only do that on a host with no other emulated network running.
EOF
