#!/usr/bin/env bash
# Bring up both packet domains, the optical line, and the UDP service.
#
#   sudo scripts/service-up.sh
#
# Steps, in the order the dependencies require:
#   1. deploy the packet topology          (the attachment containers must exist
#   2. start the optical line and attach it  before the line can bridge into them)
#   3. configure the lightpath
#   4. configure the routers               (pointless before 2: nothing crosses)
#   5. probe, then start the service
#
# The optical line runs in the background and is left running; scripts/service-down.sh
# stops everything. Re-running this script is safe only from a clean state --
# use service-down.sh first.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PACKET="$ROOT/packet-network"
OPTICAL="$ROOT/optical-network"
RUNTIME="${RUNTIME_DIR:-$ROOT/.runtime}"
OPTICAL_LOG="$RUNTIME/optical.log"
OPTICAL_PID="$RUNTIME/optical.pid"

# Client tooling. The optical line itself needs the interpreter that has the
# emulator installed, which is normally the system one.
VENV="${VENV_PYTHON:-$ROOT/.venv/bin/python}"
EMULATOR_PYTHON="${EMULATOR_PYTHON:-python3}"
BANDWIDTH="${BANDWIDTH:-1M}"

step() { printf '\n\033[1m== %s\033[0m\n' "$*"; }
fail() { printf '\nfailed: %s\n' "$*" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || fail "run with sudo: the topology and the attachment need root"
[ -x "$VENV" ] || fail "no client interpreter at $VENV -- create it with the READMEs' venv steps"

mkdir -p "$RUNTIME"

step "1/5  packet topology"
"$VENV" "$PACKET/main.py" deploy

step "2/5  optical line, attached to the packet domains"
if ss -ltn 2>/dev/null | grep -q ':8080 '; then
    fail "port 8080 is already serving an optical line; run scripts/service-down.sh first"
fi
# -u because this process's stdout is a file and therefore fully buffered:
# without it the line's own progress output would sit unflushed in the buffer.
( cd "$OPTICAL" && exec nohup "$EMULATOR_PYTHON" -u main.py start --attach >"$OPTICAL_LOG" 2>&1 ) &

printf 'waiting for the control API'
for _ in $(seq 1 60); do
    if curl -sf --max-time 2 http://localhost:8080/nodes >/dev/null 2>&1; then
        printf ' up\n'
        break
    fi
    printf '.'
    sleep 2
done
curl -sf --max-time 2 http://localhost:8080/nodes >/dev/null 2>&1 \
    || fail "the optical line did not come up; see $OPTICAL_LOG"

# Record the process that is actually serving, found by looking for it rather
# than by trusting $!. A backgrounded compound command's job id is the
# subshell, which may already have gone by the time anyone reads the file --
# signalling it would then leave the emulator running and its port held.
pgrep -f "main\.py start --attach" >"$OPTICAL_PID" || true
[ -s "$OPTICAL_PID" ] || fail "the control API is up but no optical process matched; see $OPTICAL_LOG"

# Check the attachment by looking at the ports it creates, not by grepping the
# line's log. The state is the fact; the log is only a narration of it.
for bridge in opt-a opt-b; do
    docker exec "clab-packet-qos-$bridge" ip link show eth2 >/dev/null 2>&1 \
        || fail "the optical line started but $bridge has no attachment port; see $OPTICAL_LOG"
done
echo "attached to opt-a and opt-b"

step "3/5  lightpath"
( cd "$OPTICAL" && "$EMULATOR_PYTHON" main.py configure )

step "4/5  routers"
"$VENV" "$PACKET/main.py" configure >/dev/null || fail "router configuration failed"
echo "configured both packet domains"

step "5/5  service"
# The bridges need a probe or two to learn addresses before the first one lands.
"$VENV" "$PACKET/main.py" ping --count 3 >/dev/null 2>&1 || true
"$VENV" "$PACKET/main.py" ping --count 5

"$VENV" "$PACKET/main.py" traffic start --bandwidth "$BANDWIDTH"

cat <<EOF

The service is up: client-a 10.10.0.2 -> server-b 10.20.0.2 across both packet
domains and four ROADMs.

  packet-network/main.py traffic status            what the receiver sees
  optical-network/main.py monitor                  optical margin
  packet-network/main.py path show --domain packet-a
  packet-network/main.py impair down --domain packet-a   then: path backup

  scripts/service-down.sh                          stop everything

optical line log: $OPTICAL_LOG
EOF
