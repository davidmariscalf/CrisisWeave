#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOCK_PATH = ROOT / "components.lock.json"
REGRESSION_REPOS = (
    "crisisweave-ingests",
    "crisisweave-verify",
    "crisisweave-alerts",
    "crisisweave-map",
    "crisisweave-offline",
    "crisisweave-sim",
)
ACTION_USES_RE = re.compile(r"^\s*-?\s*uses:\s*([^\s#]+)", re.MULTILINE)
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")


def run(cmd: list[str], *, cwd: Path | None = None) -> str:
    proc = subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if proc.returncode != 0:
        raise RuntimeError(
            f"command failed ({proc.returncode}): {' '.join(cmd)}\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return proc.stdout.strip()


def load_lock() -> tuple[str, dict[str, str]]:
    data = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("unsupported components.lock.json schema")
    owner = str(data.get("owner") or "").strip()
    components = data.get("components")
    if not owner or not isinstance(components, dict) or len(components) != 11:
        raise ValueError("component lock must contain owner and exactly 11 components")
    for name, sha in components.items():
        if not name.startswith("crisisweave-") or len(str(sha)) != 40 or any(c not in "0123456789abcdef" for c in str(sha)):
            raise ValueError(f"invalid component lock entry: {name}")
    return owner, {str(k): str(v) for k, v in components.items()}


def clean_component_worktree(path: Path) -> None:
    """Remove all untracked/ignored state and require a clean Git worktree."""
    run(["git", "clean", "-ffdx"], cwd=path)
    if run(["git", "status", "--porcelain"], cwd=path):
        raise RuntimeError(f"component checkout is not clean after reset: {path.name}")


def checkout_component(workspace: Path, owner: str, name: str, sha: str) -> None:
    path = workspace / name
    if path.exists() and not (path / ".git").exists():
        shutil.rmtree(path)
    if not path.exists():
        path.mkdir(parents=True)
        run(["git", "init", "-q"], cwd=path)
        run(["git", "remote", "add", "origin", f"https://github.com/{owner}/{name}.git"], cwd=path)
    else:
        remote = run(["git", "remote", "get-url", "origin"], cwd=path)
        expected = f"https://github.com/{owner}/{name}.git"
        if remote.rstrip("/") != expected.rstrip("/"):
            raise RuntimeError(f"unexpected origin for {name}: {remote}")
    run(["git", "fetch", "--depth", "1", "origin", sha], cwd=path)
    run(["git", "checkout", "--detach", "--force", "FETCH_HEAD"], cwd=path)
    # Reused workspaces must not retain untracked or ignored files from an older\n    # revision. Otherwise a supposedly pinned build can depend on stale local\n    # state that is not represented by the locked commit SHA.\n    run(["git", "clean", "-ffdx"], cwd=path)\n    if run(["git", "status", "--porcelain"], cwd=path):\n        raise RuntimeError(f"component checkout is not clean after reset: {name}")\n    actual = run(["git", "rev-parse", "HEAD"], cwd=path)
    if actual != sha:
        raise RuntimeError(f"component revision mismatch for {name}: expected {sha}, got {actual}")


def validate_workflow_pins(workspace: Path, components: dict[str, str]) -> None:
    violations: list[str] = []
    checked = 0
    for name in components:
        workflow_dir = workspace / name / ".github" / "workflows"
        if not workflow_dir.is_dir():
            continue
        for path in sorted((*workflow_dir.glob("*.yml"), *workflow_dir.glob("*.yaml"))):
            text = path.read_text(encoding="utf-8")
            for match in ACTION_USES_RE.finditer(text):
                uses = match.group(1).strip("'\"")
                if uses.startswith("./") or uses.startswith("docker://"):
                    continue
                checked += 1
                if "@" not in uses:
                    violations.append(f"{name}/{path.relative_to(workspace / name)}: missing @ref in {uses}")
                    continue
                action, ref = uses.rsplit("@", 1)
                if not action or not SHA40_RE.fullmatch(ref):
                    violations.append(
                        f"{name}/{path.relative_to(workspace / name)}: external action must use a lowercase 40-character SHA: {uses}"
                    )
    if violations:
        raise AssertionError("mutable GitHub Action references found:\n" + "\n".join(violations))
    if checked == 0:
        raise AssertionError("no external GitHub Actions were found to validate")


def run_component_regressions(workspace: Path, components: dict[str, str]) -> None:
    for name in REGRESSION_REPOS:
        if name not in components:
            raise RuntimeError(f"regression component missing from lock: {name}")
        tests = workspace / name / "tests"
        if not tests.is_dir():
            raise RuntimeError(f"expected regression tests are missing: {name}/tests")
        run(
            [sys.executable, "-W", "error::ResourceWarning", "-m", "unittest", "discover", "-s", "tests", "-v"],
            cwd=workspace / name,
        )


def verify_artifact(workspace: Path, components: dict[str, str]) -> None:
    artifact = workspace / "artifact"
    synthetic_path = artifact / "synthetic.jsonl"
    verified_path = artifact / "verified.jsonl"
    sw_path = artifact / "web" / "sw.js"
    coordinator_path = artifact / "web" / "index.html"
    volunteer_path = artifact / "web" / "volunteer.html"
    summary_path = artifact / "summary.json"

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if summary.get("repositories_combined") != len(components):
        raise AssertionError("E2E summary repository count does not match component lock")

    synthetic = [json.loads(line) for line in synthetic_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not synthetic or any(row.get("synthetic") is not True or row.get("environment") != "simulation" for row in synthetic):
        raise AssertionError("synthetic feed lost explicit simulation markers")
    if any((row.get("source") or {}).get("url") is not None for row in synthetic):
        raise AssertionError("synthetic feed unexpectedly contains source URLs")

    verified = [json.loads(line) for line in verified_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not verified or any((row.get("verification") or {}).get("method") != "crisisweave-deterministic-v2" for row in verified):
        raise AssertionError("verified feed is not using deterministic verifier v2")

    sw = sw_path.read_text(encoding="utf-8")
    forbidden = ("accept.includes('application/json')", "searchParams.has('feed')")
    if any(marker in sw for marker in forbidden):
        raise AssertionError("field package contains an unsafe broad service-worker cache rule")
    if "hasCredentials(request)" not in sw or "SNAPSHOT_URLS.has(url.href)" not in sw:
        raise AssertionError("field package is missing hardened service-worker cache boundaries")

    coordinator = coordinator_path.read_text(encoding="utf-8")
    if "u.origin!==location.origin" not in coordinator or "MAX_SNAPSHOT_BYTES=5*1024*1024" not in coordinator:
        raise AssertionError("coordinator field package lost the same-origin snapshot boundary")

    volunteer = volunteer_path.read_text(encoding="utf-8")
    if "q.get('api')" in volunteer or "Live operational API" in volunteer:
        raise AssertionError("volunteer package can still access an operational API directly")
    for required in ("u.origin!==location.origin", "MAX_SNAPSHOT_BYTES=5*1024*1024", "crisisweave:last-worksites-public"):
        if required not in volunteer:
            raise AssertionError(f"volunteer public-snapshot guard missing: {required}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run CrisisWeave E2E from locked tested component revisions")
    parser.add_argument("--workspace", default="./crisisweave-demo")
    parser.add_argument("--count", type=int, default=45)
    args = parser.parse_args()

    owner, components = load_lock()
    workspace = Path(args.workspace).resolve()
    workspace.mkdir(parents=True, exist_ok=True)

    for name, sha in components.items():
        checkout_component(workspace, owner, name, sha)

    # Supply-chain invariant: every external action in every locked component
    # must be immutable, not a branch/tag such as @main or @v4.
    validate_workflow_pins(workspace, components)

    # The integration script already runs the cores, worksites and platform
    # suites. Run the remaining module regressions here so every component with
    # a unit-test suite is exercised at the exact locked revision.
    run_component_regressions(workspace, components)

    cmd = [
        sys.executable,
        str(ROOT / "integrate.py"),
        "--workspace",
        str(workspace),
        "--skip-clone",
        "--count",
        str(args.count),
    ]
    proc = subprocess.run(cmd, text=True, check=False)
    if proc.returncode != 0:
        return proc.returncode

    verify_artifact(workspace, components)
    print(json.dumps({"ok": True, "locked_components": len(components), "regression_suites": len(REGRESSION_REPOS) + 3, "workflow_pins": "immutable", "artifact": str(workspace / "artifact")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
