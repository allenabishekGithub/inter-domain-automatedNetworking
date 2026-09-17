#!/usr/bin/env bash
# Run both component test suites.
#
# They run in separate pytest sessions on purpose: each component keeps its
# modules at its own root and both define a top-level main.py, so sharing one
# interpreter's module namespace would make whichever is imported second lose.

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${VENV_PYTHON:-$ROOT/.venv/bin/python}"
failed=()

for component in packet-network optical-network; do
    printf '\n\033[1m== %s\033[0m\n' "$component"
    ( cd "$ROOT/$component" && "$PYTHON" -m pytest -p no:cacheprovider ) || failed+=("$component")
done

if [ ${#failed[@]} -gt 0 ]; then
    printf '\nFAILED: %s\n' "${failed[*]}"
    exit 1
fi
printf '\nBoth suites passed.\n'
