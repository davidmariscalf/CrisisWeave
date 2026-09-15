#!/usr/bin/env bash
set -euo pipefail

WORKDIR="${1:-./crisisweave-demo}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN=python
fi

"$PYTHON_BIN" "$(dirname "$0")/production_check.py"
"$PYTHON_BIN" "$(dirname "$0")/run_pinned.py" --workspace "$WORKDIR"

printf '\nCrisisWeave locked E2E artifact created in: %s/artifact\n' "$WORKDIR"
printf 'Verify the sealed artifact with:\n'
printf '  %s %s/seal_artifact.py %s/artifact --verify\n' "$PYTHON_BIN" "$(dirname "$0")" "$WORKDIR"
printf 'To inspect the field console:\n'
printf '  cd %s/artifact && python -m http.server 8765 -d web\n' "$WORKDIR"
printf '  open http://localhost:8765/index.html\n'
