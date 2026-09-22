#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import integrate

ROOT = Path(__file__).resolve().parent
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
ACTION_USES_RE = re.compile(r"^\s*-?\s*uses:\s*([^\s#]+)", re.MULTILINE)
REQUIRED_FILES = (
    ".editorconfig",
    "components.lock.json",
    "integrate.py",
    "case_studies.py",
    "CASE_STUDIES.md",
    "run_pinned.py",
    "seal_artifact.py",
    "schema/event.schema.json",
    "PRODUCTION.md",
    "LICENSING_AUDIT.md",
    ".github/workflows/cross-repo-e2e.yml",
    ".github/workflows/quality.yml",
    "tests/offline_browser_smoke.mjs",
)
FORBIDDEN_TRACKED_BASENAMES = {".env", "id_rsa", "id_ed25519"}
FORBIDDEN_TRACKED_SUFFIXES = {".pem", ".key", ".p12", ".pfx"}
TEXT_SUFFIXES = {"", ".md", ".txt", ".json", ".yml", ".yaml", ".toml", ".py", ".js", ".mjs", ".ts", ".html", ".css", ".sh", ".ps1"}
PRIVATE_KEY_MARKER = "-----BEGIN " + "PRIVATE KEY-----"
HIGH_CONFIDENCE_SECRET_PATTERNS = (
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"Bearer\\s+[A-Za-z0-9._~+/-]{20,}", re.IGNORECASE),
)
SECRET_ASSIGNMENT_RE = re.compile(
    r"(?im)^\\s*([A-Za-z_][A-Za-z0-9_.-]*(?:api[_-]?key|token|secret|password|private[_-]?key|client[_-]?secret)[A-Za-z0-9_.-]*)\\s*[:=]\\s*['\\\"]?([^#\\s'\\\"]{16,})"
)
PLACEHOLDER_MARKERS = ("EXAMPLE", "CHANGEME", "REPLACE_", "YOUR_", "<", "$\\{")


def check_python() -> None:
    if sys.version_info < (3, 11):
        raise RuntimeError(f"Python 3.11+ is required; found {sys.version.split()[0]}")


def check_required_files() -> None:
    missing = [rel for rel in REQUIRED_FILES if not (ROOT / rel).is_file()]
    if missing:
        raise RuntimeError(f"required repository files are missing: {', '.join(missing)}")


def check_component_lock() -> int:
    data = json.loads((ROOT / "components.lock.json").read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise RuntimeError("unsupported components.lock.json schema")
    if data.get("owner") != "davidmariscalf":
        raise RuntimeError("unexpected component owner")
    components = data.get("components")
    if not isinstance(components, dict) or len(components) != 11:
        raise RuntimeError("component lock must contain exactly 11 repositories")
    for name, sha in components.items():
        if not str(name).startswith("crisisweave-") or not SHA40_RE.fullmatch(str(sha)):
            raise RuntimeError(f"invalid locked component: {name}")
    if set(components) != set(integrate.REPOS):
        missing = sorted(set(integrate.REPOS) - set(components))
        extra = sorted(set(components) - set(integrate.REPOS))
        raise RuntimeError(f"component lock and integrator disagree; missing={missing}, extra={extra}")
    return len(components)


def check_json_schema() -> None:
    schema = json.loads((ROOT / "schema/event.schema.json").read_text(encoding="utf-8"))
    if not isinstance(schema, dict) or not schema.get("$schema"):
        raise RuntimeError("event schema is not a valid JSON Schema document")


def check_python_sources() -> None:
    for rel in ("integrate.py", "case_studies.py", "run_pinned.py", "seal_artifact.py", "production_check.py"):
        source = (ROOT / rel).read_text(encoding="utf-8")
        compile(source, str(ROOT / rel), "exec")


def check_workflow_pins() -> int:
    workflow_dir = ROOT / ".github" / "workflows"
    checked = 0
    violations: list[str] = []
    for path in sorted((*workflow_dir.glob("*.yml"), *workflow_dir.glob("*.yaml"))):
        text = path.read_text(encoding="utf-8")
        for match in ACTION_USES_RE.finditer(text):
            uses = match.group(1).strip("'\"")
            if uses.startswith("./") or uses.startswith("docker://"):
                continue
            checked += 1
            if "@" not in uses:
                violations.append(f"{path.relative_to(ROOT)}: missing @ref in {uses}")
                continue
            action, ref = uses.rsplit("@", 1)
            if not action or not SHA40_RE.fullmatch(ref):
                violations.append(f"{path.relative_to(ROOT)}: mutable action reference {uses}")
    if violations:
        raise RuntimeError("mutable GitHub Action references found:\n" + "\n".join(violations))
    if checked == 0:
        raise RuntimeError("no external GitHub Actions were found to validate")
    return checked


def check_browser_smoke() -> None:
    workflow = (ROOT / ".github" / "workflows" / "cross-repo-e2e.yml").read_text(encoding="utf-8")
    required = (
        "playwright@1.63.0",
        "playwright install --with-deps chromium",
        "tests/offline_browser_smoke.mjs",
        "Cold-start field package with network disabled",
    )
    missing = [item for item in required if item not in workflow]
    if missing:
        raise RuntimeError("offline browser smoke workflow is incomplete: " + ", ".join(missing))


def check_launchers() -> None:
    for rel in ("demo.sh", "demo.ps1"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        if "run_pinned.py" not in text:
            raise RuntimeError(f"{rel} does not use the locked runner")
        if "production_check.py" not in text:
            raise RuntimeError(f"{rel} does not run the production preflight")
        if "seal_artifact.py" not in text or "--lock" not in text:
            raise RuntimeError(f"{rel} does not seal the release artifact")
        if "integrate.py" in text:
            raise RuntimeError(f"{rel} bypasses the locked runner")


def check_git_and_tracked_secrets() -> int:
    if shutil.which("git") is None:
        raise RuntimeError("git is required")
    proc = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git ls-files failed: {proc.stderr.strip()}")

    filenames: list[str] = []
    content_violations: list[str] = []
    scanned = 0

    for raw in proc.stdout.splitlines():
        rel = raw.strip()
        if not rel:
            continue
        path = Path(rel)
        if path.name in FORBIDDEN_TRACKED_BASENAMES or path.suffix.lower() in FORBIDDEN_TRACKED_SUFFIXES:
            filenames.append(rel)
            continue

        full = ROOT / path
        if path.suffix.lower() not in TEXT_SUFFIXES or not full.is_file():
            continue
        try:
            text = full.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        scanned += 1
        if PRIVATE_KEY_MARKER in text:
            content_violations.append(f"{rel}: private-key material")

        for pattern in HIGH_CONFIDENCE_SECRET_PATTERNS:
            if pattern.search(text):
                content_violations.append(f"{rel}: high-confidence credential pattern")
                break

        for match in SECRET_ASSIGNMENT_RE.finditer(text):
            value = match.group(2)
            upper = value.upper()
            if any(marker in upper for marker in PLACEHOLDER_MARKERS):
                continue
            if value.startswith(("http://", "https://", "/")):
                continue
            content_violations.append(f"{rel}: possible populated secret assignment")
            break

    if filenames:
        raise RuntimeError("potential secret-bearing files are tracked: " + ", ".join(filenames))
    if content_violations:
        raise RuntimeError("potential secret material found in tracked content: " + ", ".join(content_violations))
    return scanned


def main() -> int:
    check_python()
    check_required_files()
    components = check_component_lock()
    check_json_schema()
    check_python_sources()
    actions = check_workflow_pins()
    check_browser_smoke()
    check_launchers()
    secret_files_scanned = check_git_and_tracked_secrets()
    print(json.dumps({
        "ok": True,
        "python": sys.version.split()[0],
        "locked_components": components,
        "immutable_actions_checked": actions,
        "offline_browser_smoke": "pinned",
        "launchers": "locked_and_sealed",
        "tracked_secret_filenames": "clear",
        "tracked_secret_content": "clear",
        "tracked_text_files_scanned": secret_files_scanned,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
