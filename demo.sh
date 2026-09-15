#!/usr/bin/env bash
set -euo pipefail

WORKDIR="${1:-./crisisweave-demo}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN=python
fi

"$PYTHON_BIN" "$SCRIPT_DIR/production_check.py"
"$PYTHON_BIN" "$SCRIPT_DIR/run_pinned.py" --workspace "$WORKDIR"
"$PYTHON_BIN" "$SCRIPT_DIR/seal_artifact.py" "$WORKDIR/artifact" --lock "$SCRIPT_DIR/components.lock.json"

printf '\nCrisisWeave locked and sealed E2E artifact created in: %s/artifact\n' "$WORKDIR"
printf 'Verify it again with:\n'
printf '  %s %s/seal_artifact.py %s/artifact --verify\n' "$PYTHON_BIN" "$SCRIPT_DIR" "$WORKDIR"
printf 'To inspect the field console:\n'
printf '  cd %s/artifact && python -m http.server 8765 -d web\n' "$WORKDIR"
printf '  open http://localhost:8765/index.html\n'
