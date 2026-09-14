#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

OWNER = "davidmariscalf"
REPOS = (
    "crisisweave-ingests",
    "crisisweave-verify",
    "crisisweave-map",
    "crisisweave-offline",
    "crisisweave-alerts",
    "crisisweave-sim",
    "crisisweave-docs",
)

CAP_SAMPLE = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<alert xmlns=\"urn:oasis:names:tc:emergency:cap:1.2\">
  <identifier>CW-DEMO-CAP-001</identifier>
  <sender>demo-authority@example.invalid</sender>
  <sent>2026-01-01T12:03:00+00:00</sent>
  <status>Actual</status>
  <msgType>Alert</msgType>
  <scope>Public</scope>
  <info>
    <category>Met</category>
    <event>Flood</event>
    <urgency>Immediate</urgency>
    <severity>Severe</severity>
    <certainty>Likely</certainty>
    <effective>2026-01-01T12:03:00+00:00</effective>
    <headline>River flooding reported</headline>
    <description>Water levels are rising across the synthetic test district.</description>
    <area><areaDesc>Synthetic River District</areaDesc></area>
  </info>
</alert>
"""

JSON_SAMPLE = {
    "events": [
        {
            "id": "cw-demo-json-001",
            "title": "River flooding reported",
            "description": "Water levels are rising across the synthetic test district.",
            "observed_at": "2026-01-01T12:05:00+00:00",
            "severity": 0.82,
            "confidence": 0.74,
            "official": False,
            "area": "Synthetic River District",
            "source": "Synthetic Municipal Sensor",
            "geometry": {"type": "Point", "coordinates": [-3.7038, 40.4168]},
        }
    ]
}

RULES = [
    {"id": "high-severity-flood", "kinds": ["flood"], "min_severity": 0.7, "min_confidence": 0.7},
    {"id": "high-severity-wildfire", "kinds": ["wildfire"], "min_severity": 0.75, "min_confidence": 0.7},
    {"id": "official-severe", "min_severity": 0.75, "min_confidence": 0.7, "official_only": True},
]


def run(cmd: list[str], *, cwd: Path | None = None, stdin: str | None = None) -> str:
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        input=stdin,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"command failed ({proc.returncode}): {' '.join(cmd)}\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return proc.stdout


def ensure_repo(workspace: Path, name: str, *, skip_clone: bool) -> Path:
    path = workspace / name
    if skip_clone:
        if not path.exists():
            raise FileNotFoundError(f"--skip-clone requires {path}")
        return path

    if (path / ".git").exists():
        run(["git", "-C", str(path), "pull", "--ff-only"])
    elif path.exists():
        raise RuntimeError(f"{path} exists but is not a git checkout")
    else:
        run(["git", "clone", "--depth", "1", f"https://github.com/{OWNER}/{name}.git", str(path)])
    return path


def jsonl(text: str) -> list[dict]:
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the public CrisisWeave repositories as one end-to-end system")
    parser.add_argument("--workspace", default="./crisisweave-demo", help="Checkout and artifact directory")
    parser.add_argument("--skip-clone", action="store_true", help="Use repositories already present inside the workspace")
    parser.add_argument("--count", type=int, default=45, help="Number of deterministic synthetic reports")
    args = parser.parse_args()
    if not 3 <= args.count <= 100000:
        raise SystemExit("--count must be between 3 and 100000")

    workspace = Path(args.workspace).resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    repos = {name: ensure_repo(workspace, name, skip_clone=args.skip_clone) for name in REPOS}

    artifact = workspace / "artifact"
    if artifact.exists():
        shutil.rmtree(artifact)
    artifact.mkdir(parents=True)

    synthetic = run([
        sys.executable,
        str(repos["crisisweave-sim"] / "simulate.py"),
        "--scenario", "mixed", "--count", str(args.count), "--seed", "42",
    ])
    (artifact / "synthetic.jsonl").write_text(synthetic, encoding="utf-8")

    cap_path = artifact / "sample-cap.xml"
    cap_path.write_text(CAP_SAMPLE, encoding="utf-8")
    cap = run([
        sys.executable,
        str(repos["crisisweave-ingests"] / "crisisweave_ingests.py"),
        "cap", str(cap_path), "--source-url", "https://example.invalid/cap/demo",
    ])
    (artifact / "cap.jsonl").write_text(cap, encoding="utf-8")

    json_path = artifact / "sample-feed.json"
    json_path.write_text(json.dumps(JSON_SAMPLE, indent=2), encoding="utf-8")
    generic = run([
        sys.executable,
        str(repos["crisisweave-ingests"] / "crisisweave_ingests.py"),
        "json", str(json_path), "--source-url", "https://example.invalid/json/demo",
    ])
    (artifact / "generic.jsonl").write_text(generic, encoding="utf-8")

    raw = synthetic + cap + generic
    (artifact / "raw.jsonl").write_text(raw, encoding="utf-8")

    verified = run([sys.executable, str(repos["crisisweave-verify"] / "verifier.py")], stdin=raw)
    (artifact / "verified.jsonl").write_text(verified, encoding="utf-8")

    rules_path = artifact / "rules.json"
    rules_path.write_text(json.dumps(RULES, indent=2), encoding="utf-8")
    alerts = run([
        sys.executable,
        str(repos["crisisweave-alerts"] / "alerts.py"),
        str(rules_path),
    ], stdin=verified)
    (artifact / "alerts.jsonl").write_text(alerts, encoding="utf-8")

    web = artifact / "web"
    web.mkdir()
    shutil.copy2(repos["crisisweave-map"] / "index.html", web / "index.html")
    shutil.copy2(repos["crisisweave-offline"] / "sw.js", web / "sw.js")
    shutil.copy2(artifact / "verified.jsonl", web / "verified.jsonl")
    shutil.copy2(artifact / "alerts.jsonl", web / "alerts.jsonl")
    (web / "OPEN_ME.txt").write_text(
        "VOLUNTEER VIEW\n"
        "==============\n"
        "Serve this directory over HTTP and open index.html.\n"
        "The console automatically loads verified.jsonl and alerts.jsonl.\n\n"
        "Example:\n"
        "  python -m http.server 8765 -d web\n\n"
        "Then visit:\n"
        "  http://localhost:8765/index.html\n\n"
        "Operators may override feeds with ?feed=...&alerts=... when needed.\n",
        encoding="utf-8",
    )

    docs = artifact / "docs"
    docs.mkdir()
    for name in ("ARCHITECTURE.md", "THREAT_MODEL.md"):
        src = repos["crisisweave-docs"] / name
        if not src.exists():
            raise FileNotFoundError(f"required documentation missing: {src}")
        shutil.copy2(src, docs / name)

    raw_events = jsonl(raw)
    verified_events = jsonl(verified)
    alert_events = jsonl(alerts)
    if len(raw_events) != args.count + 2:
        raise AssertionError(f"expected {args.count + 2} raw events, got {len(raw_events)}")
    if not 1 <= len(verified_events) <= len(raw_events):
        raise AssertionError("verifier produced an impossible event count")
    if not alert_events:
        raise AssertionError("expected at least one alert match")
    if not any(e.get("source", {}).get("type") == "cap" for e in raw_events):
        raise AssertionError("CAP ingest path did not produce an event")
    if not any(e.get("geometry") for e in verified_events):
        raise AssertionError("no map-ready geometry survived verification")
    if not (web / "verified.jsonl").exists() or not (web / "alerts.jsonl").exists():
        raise AssertionError("field console feeds were not packaged")

    summary = {
        "repositories_combined": len(REPOS),
        "raw_reports": len(raw_events),
        "verified_incidents": len(verified_events),
        "alerts": len(alert_events),
        "map_ready_incidents": sum(bool(e.get("geometry")) for e in verified_events),
        "artifact": str(artifact),
        "web_console": str(web),
        "volunteer_console": "index.html (auto-loads verified + alert feeds)",
        "safety": "Synthetic data only in this demo; not an emergency authority.",
    }
    (artifact / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
