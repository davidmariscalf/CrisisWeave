#!/usr/bin/env bash
set -euo pipefail

WORKDIR="${1:-./crisisweave-demo}"
mkdir -p "$WORKDIR"
cd "$WORKDIR"

clone_or_update() {
  local repo="$1"
  if [ -d "$repo/.git" ]; then
    git -C "$repo" pull --ff-only
  else
    git clone "https://github.com/davidmariscalf/$repo.git"
  fi
}

clone_or_update crisisweave-sim
clone_or_update crisisweave-verify
clone_or_update crisisweave-alerts

python crisisweave-sim/simulate.py --scenario mixed --count 30 --seed 42 > events.jsonl
python crisisweave-verify/verifier.py < events.jsonl > verified.jsonl

cat > rules.json <<'JSON'
[
  {
    "id": "high-severity-flood",
    "kinds": ["flood"],
    "min_severity": 0.7,
    "min_confidence": 0.7
  },
  {
    "id": "high-severity-wildfire",
    "kinds": ["wildfire"],
    "min_severity": 0.75,
    "min_confidence": 0.7
  }
]
JSON

python crisisweave-alerts/alerts.py rules.json < verified.jsonl > alerts.jsonl

printf '\nCrisisWeave demo complete.\n'
printf 'Raw events:      %s\n' "$(wc -l < events.jsonl | tr -d ' ')"
printf 'Verified events: %s\n' "$(wc -l < verified.jsonl | tr -d ' ')"
printf 'Alert matches:   %s\n' "$(wc -l < alerts.jsonl | tr -d ' ')"
printf '\nFiles written to %s\n' "$(pwd)"
printf 'Open verified.jsonl in crisisweave-map to inspect mapped events.\n'
