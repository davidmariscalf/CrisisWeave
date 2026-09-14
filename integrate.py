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
    "crisisweave-cores",
    "crisisweave-ingests",
    "crisisweave-verify",
    "crisisweave-alerts",
    "crisisweave-worksites",
    "crisisweave-platform",
    "crisisweave-map",
    "crisisweave-offline",
    "crisisweave-sim",
    "crisisweave-docs",
    "crisisweave-infra",
)

CAP_SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<alert xmlns="urn:oasis:names:tc:emergency:cap:1.2">
  <identifier>CW-DEMO-CAP-001</identifier><sender>demo-authority@example.invalid</sender>
  <sent>2026-01-01T12:03:00+00:00</sent><status>Actual</status><msgType>Alert</msgType><scope>Public</scope>
  <info><category>Met</category><event>Flood</event><urgency>Immediate</urgency><severity>Severe</severity><certainty>Likely</certainty>
  <effective>2026-01-01T12:03:00+00:00</effective><headline>River flooding reported</headline>
  <description>Water levels are rising across the synthetic test district.</description><area><areaDesc>Synthetic River District</areaDesc></area></info>
</alert>
"""

JSON_SAMPLE = {"events": [{
    "id": "cw-demo-json-001", "title": "River flooding reported",
    "description": "Water levels are rising across the synthetic test district.",
    "observed_at": "2026-01-01T12:05:00+00:00", "severity": 0.82, "confidence": 0.74,
    "official": False, "area": "Synthetic River District", "source": "Synthetic Municipal Sensor",
    "geometry": {"type": "Point", "coordinates": [-3.7038, 40.4168]},
}]}

RULES = [
    {"id": "high-severity-flood", "kinds": ["flood"], "min_severity": 0.7, "min_confidence": 0.7},
    {"id": "high-severity-wildfire", "kinds": ["wildfire"], "min_severity": 0.75, "min_confidence": 0.7},
    {"id": "official-severe", "min_severity": 0.75, "min_confidence": 0.7, "official_only": True},
]


def run(cmd: list[str], *, cwd: Path | None = None, stdin: str | None = None) -> str:
    proc = subprocess.run(cmd, cwd=cwd, input=stdin, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"command failed ({proc.returncode}): {' '.join(cmd)}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}")
    return proc.stdout


def ensure_repo(workspace: Path, name: str, *, skip_clone: bool) -> Path:
    path = workspace / name
    if skip_clone:
        if not path.exists(): raise FileNotFoundError(f"--skip-clone requires {path}")
        return path
    if (path / ".git").exists(): run(["git", "-C", str(path), "pull", "--ff-only"])
    elif path.exists(): raise RuntimeError(f"{path} exists but is not a git checkout")
    else: run(["git", "clone", "--depth", "1", f"https://github.com/{OWNER}/{name}.git", str(path)])
    return path


def jsonl(text: str) -> list[dict]:
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the public CrisisWeave repositories as one end-to-end system")
    parser.add_argument("--workspace", default="./crisisweave-demo")
    parser.add_argument("--skip-clone", action="store_true")
    parser.add_argument("--count", type=int, default=45)
    args = parser.parse_args()
    if not 3 <= args.count <= 100000: raise SystemExit("--count must be between 3 and 100000")

    workspace = Path(args.workspace).resolve(); workspace.mkdir(parents=True, exist_ok=True)
    repos = {name: ensure_repo(workspace, name, skip_clone=args.skip_clone) for name in REPOS}
    artifact = workspace / "artifact"
    if artifact.exists(): shutil.rmtree(artifact)
    artifact.mkdir(parents=True)

    synthetic = run([sys.executable, str(repos["crisisweave-sim"] / "simulate.py"), "--scenario", "mixed", "--count", str(args.count), "--seed", "42"])
    (artifact / "synthetic.jsonl").write_text(synthetic, encoding="utf-8")

    cap_path = artifact / "sample-cap.xml"; cap_path.write_text(CAP_SAMPLE, encoding="utf-8")
    cap = run([sys.executable, str(repos["crisisweave-ingests"] / "crisisweave_ingests.py"), "cap", str(cap_path), "--source-url", "https://example.invalid/cap/demo"])
    (artifact / "cap.jsonl").write_text(cap, encoding="utf-8")

    json_path = artifact / "sample-feed.json"; json_path.write_text(json.dumps(JSON_SAMPLE, indent=2), encoding="utf-8")
    generic = run([sys.executable, str(repos["crisisweave-ingests"] / "crisisweave_ingests.py"), "json", str(json_path), "--source-url", "https://example.invalid/json/demo"])
    (artifact / "generic.jsonl").write_text(generic, encoding="utf-8")

    raw = synthetic + cap + generic; (artifact / "raw.jsonl").write_text(raw, encoding="utf-8")
    verified = run([sys.executable, str(repos["crisisweave-verify"] / "verifier.py")], stdin=raw)
    verified_path = artifact / "verified.jsonl"; verified_path.write_text(verified, encoding="utf-8")

    rules_path = artifact / "rules.json"; rules_path.write_text(json.dumps(RULES, indent=2), encoding="utf-8")
    alerts = run([sys.executable, str(repos["crisisweave-alerts"] / "alerts.py"), str(rules_path)], stdin=verified)
    alerts_path = artifact / "alerts.jsonl"; alerts_path.write_text(alerts, encoding="utf-8")

    # Recovery work comes from the dedicated operational module and is never inferred from hazard proximity.
    worksites_repo = repos["crisisweave-worksites"]
    worksites_script = worksites_repo / "worksites.py"
    examples = worksites_repo / "examples" / "worksites.jsonl"
    work_db = artifact / "worksites.db"
    run([sys.executable, str(worksites_script), "--db", str(work_db), "validate", str(examples)])
    run([sys.executable, str(worksites_script), "--db", str(work_db), "import", str(examples)])
    run([sys.executable, str(worksites_script), "--db", str(work_db), "assign", "cw-work-001", "--team", "demo-response-team", "--actor", "e2e-coordinator"])
    worksites = run([sys.executable, str(worksites_script), "--db", str(work_db), "export"])
    worksites_path = artifact / "worksites.jsonl"; worksites_path.write_text(worksites, encoding="utf-8")

    # Shared public guardrails are exercised against incident and worksite outputs.
    contracts = repos["crisisweave-cores"] / "contracts.py"
    run([sys.executable, str(contracts), "check", "--kind", "event", str(verified_path)])
    run([sys.executable, str(contracts), "check", "--kind", "worksite", str(worksites_path)])

    # The platform is part of the E2E path, not a decorative deployment repo.
    platform_repo = repos["crisisweave-platform"]
    run([sys.executable, "-W", "error::ResourceWarning", "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=platform_repo)
    platform_state = artifact / "platform-state"; platform_state.mkdir()
    platform_db = platform_state / "platform.db"; private_db = platform_state / "private.db"
    platform_script = platform_repo / "crisisweave_platform.py"
    pepper = "synthetic-e2e-pepper-value-not-for-production"
    base = [sys.executable, str(platform_script), "--db", str(platform_db), "--private-db", str(private_db), "--pepper", pepper]
    run(base + ["init"])
    run(base + ["create-org", "demo-relief", "Demo Relief"])
    run(base + ["create-principal", "coord-e2e", "--org", "demo-relief", "--name", "E2E Coordinator", "--role", "coordinator"])
    issued = json.loads(run(base + ["issue-token", "coord-e2e"]))
    token = issued.get("token", "")
    if not token.startswith("cw_"): raise AssertionError("platform did not issue a CrisisWeave bearer token")
    if token.encode() in platform_db.read_bytes(): raise AssertionError("raw platform token was stored in SQLite")

    platform_docs = artifact / "platform"; platform_docs.mkdir()
    for name in ("SECURITY.md", "DEPLOYMENT.md", "compose.yaml"):
        shutil.copy2(platform_repo / name, platform_docs / name)

    # Infrastructure is validated as part of the public system and copied into the E2E artifact.
    infra_repo = repos["crisisweave-infra"]
    infra_required = (
        "site/index.html", "site/_headers", "site/_redirects", "site/health.json",
        "site/robots.txt", "site/sitemap.xml", "site/.well-known/security.txt",
        "netlify.toml", ".env.example", "scripts/check-secrets.py",
    )
    for rel in infra_required:
        if not (infra_repo / rel).exists(): raise AssertionError(f"infrastructure repo missing {rel}")
    run([sys.executable, str(infra_repo / "scripts" / "check-secrets.py")], cwd=infra_repo)
    infra_artifact = artifact / "infra"
    shutil.copytree(infra_repo / "site", infra_artifact / "site")
    shutil.copy2(infra_repo / "netlify.toml", infra_artifact / "netlify.toml")

    web = artifact / "web"; web.mkdir()
    for name in ("index.html", "volunteer.html"): shutil.copy2(repos["crisisweave-map"] / name, web / name)
    shutil.copy2(repos["crisisweave-offline"] / "sw.js", web / "sw.js")
    for name in ("verified.jsonl", "alerts.jsonl", "worksites.jsonl"): shutil.copy2(artifact / name, web / name)
    (web / "OPEN_ME.txt").write_text(
        "CRISISWEAVE FIELD PACKAGE\n=========================\n"
        "Static mode:\n  python -m http.server 8765 -d web\n"
        "  Volunteer: http://localhost:8765/volunteer.html\n"
        "  Coordinator: http://localhost:8765/index.html\n\n"
        "Operational worksite API (second terminal, from the workspace root):\n"
        "  python crisisweave-worksites/worksites.py --db artifact/worksites.db serve --port 8787\n\n"
        "Authenticated platform API is provided by crisisweave-platform. See artifact/platform/DEPLOYMENT.md.\n"
        "The public demo is synthetic and is not emergency dispatch.\n", encoding="utf-8")

    docs = artifact / "docs"; docs.mkdir()
    for name in ("ARCHITECTURE.md", "THREAT_MODEL.md"):
        src = repos["crisisweave-docs"] / name
        if not src.exists(): raise FileNotFoundError(f"required documentation missing: {src}")
        shutil.copy2(src, docs / name)

    raw_events, verified_events, alert_events, worksite_events = jsonl(raw), jsonl(verified), jsonl(alerts), jsonl(worksites)
    if len(raw_events) != args.count + 2: raise AssertionError(f"expected {args.count + 2} raw events, got {len(raw_events)}")
    if not 1 <= len(verified_events) <= len(raw_events): raise AssertionError("verifier produced an impossible event count")
    if not alert_events: raise AssertionError("expected at least one alert match")
    if not worksite_events: raise AssertionError("worksite module exported no records")
    if any((w.get("source") or {}).get("type") != "synthetic" for w in worksite_events): raise AssertionError("public E2E worksites must remain synthetic")
    if not any(w.get("state") == "assigned" and w.get("assigned_team") == "demo-response-team" for w in worksite_events): raise AssertionError("worksite assignment path was not exercised")
    if not any(e.get("source", {}).get("type") == "cap" for e in raw_events): raise AssertionError("CAP ingest path did not produce an event")
    if not any(e.get("geometry") for e in verified_events): raise AssertionError("no map-ready geometry survived verification")
    for required in ("index.html", "volunteer.html", "verified.jsonl", "alerts.jsonl", "worksites.jsonl", "sw.js"):
        if not (web / required).exists(): raise AssertionError(f"field package missing {required}")
    for required in (platform_db, private_db, platform_docs / "DEPLOYMENT.md", infra_artifact / "site" / "_headers", infra_artifact / "site" / "health.json"):
        if not required.exists(): raise AssertionError(f"deployment artifact missing {required}")

    summary = {
        "repositories_combined": len(REPOS),
        "raw_reports": len(raw_events),
        "verified_incidents": len(verified_events),
        "alerts": len(alert_events),
        "demo_worksites": len(worksite_events),
        "assigned_demo_worksites": sum(w.get("state") == "assigned" for w in worksite_events),
        "map_ready_incidents": sum(bool(e.get("geometry")) for e in verified_events),
        "public_contract_checks": "passed",
        "platform_tests": "passed",
        "platform_identity_bootstrap": "passed",
        "raw_token_storage_check": "passed",
        "infrastructure_checks": "passed",
        "artifact": str(artifact),
        "coordinator_console": "web/index.html",
        "volunteer_console": "web/volunteer.html",
        "worksite_database": "worksites.db",
        "platform_state": "platform-state/",
        "public_site_bundle": "infra/site/",
        "safety": "Synthetic data only; not an emergency authority or dispatch system.",
    }
    (artifact / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2)); return 0


if __name__ == "__main__": raise SystemExit(main())
