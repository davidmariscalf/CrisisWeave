from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable


def _jsonl(text: str) -> list[dict[str, Any]]:
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def build_case_studies(
    repos: dict[str, Path],
    artifact: Path,
    run: Callable[..., str],
) -> dict[str, Any]:
    """Build deterministic synthetic case studies from the locked CrisisWeave components.

    These scenarios are evaluation fixtures, not claims of real-world deployment.
    They make the editorial examples reproducible from the same release artifact.
    """
    out = artifact / "case-studies"
    out.mkdir(parents=True, exist_ok=True)

    fragmented_reports = [
        {
            "id": "case-flood-cap-001",
            "synthetic": True,
            "environment": "case-study",
            "kind": "flood",
            "title": "River flooding affecting low-lying roads",
            "description": "Water is rising across the synthetic Riverside district.",
            "observed_at": "2026-01-01T12:00:00Z",
            "expires_at": None,
            "severity": 0.78,
            "confidence": 0.82,
            "official": True,
            "geometry": {"type": "Point", "coordinates": [-3.7038, 40.4168]},
            "area": "Synthetic Riverside District",
            "source": {
                "name": "Synthetic Emergency Agency",
                "type": "cap",
                "url": "https://example.invalid/case/flood/cap",
                "source_id": "CAP-FLOOD-001",
            },
            "tags": ["synthetic", "case-study", "flood"],
        },
        {
            "id": "case-flood-field-002",
            "synthetic": True,
            "environment": "case-study",
            "kind": "flood",
            "title": "River flooding affecting low-lying roads",
            "description": "Water is rising across the synthetic Riverside district.",
            "observed_at": "2026-01-01T12:20:00Z",
            "expires_at": None,
            "severity": 0.93,
            "confidence": 0.55,
            "official": False,
            "geometry": {"type": "Point", "coordinates": [-3.7040, 40.4169]},
            "area": "Synthetic Riverside District",
            "source": {
                "name": "Synthetic Volunteer Network",
                "type": "field",
                "url": None,
                "source_id": "FIELD-FLOOD-002",
            },
            "tags": ["synthetic", "case-study", "flood"],
        },
    ]
    fragmented_input = out / "fragmented-flood-input.jsonl"
    _write_jsonl(fragmented_input, fragmented_reports)
    verified_text = run(
        [sys.executable, str(repos["crisisweave-verify"] / "verifier.py")],
        stdin=fragmented_input.read_text(encoding="utf-8"),
    )
    verified_rows = _jsonl(verified_text)
    if len(verified_rows) != 1:
        raise AssertionError("fragmented flood case must merge into exactly one incident")
    merged = verified_rows[0]
    verification = merged.get("verification") or {}
    evidence = merged.get("evidence") or []
    if verification.get("report_count") != 2 or verification.get("independent_source_count") != 2:
        raise AssertionError("fragmented flood case lost corroboration counts")
    if {entry.get("source_id") for entry in evidence} != {"CAP-FLOOD-001", "FIELD-FLOOD-002"}:
        raise AssertionError("fragmented flood case lost report-level provenance")
    _write_jsonl(out / "fragmented-flood-verified.jsonl", verified_rows)

    freshness_events = [
        {
            "id": "case-wildfire-stale",
            "kind": "wildfire",
            "title": "Wildfire near synthetic ridge",
            "description": "Synthetic wildfire report used to test freshness rules.",
            "observed_at": "2026-01-01T08:00:00Z",
            "expires_at": None,
            "severity": 0.90,
            "confidence": 0.90,
            "official": True,
            "area": "Synthetic Pine Ridge",
            "source": {"name": "Synthetic Emergency Agency", "type": "cap", "source_id": "WF-STALE"},
        },
        {
            "id": "case-wildfire-fresh",
            "kind": "wildfire",
            "title": "Wildfire near synthetic ridge",
            "description": "Synthetic wildfire report used to test freshness rules.",
            "observed_at": "2026-01-01T11:30:00Z",
            "expires_at": None,
            "severity": 0.85,
            "confidence": 0.72,
            "official": False,
            "area": "Synthetic Pine Ridge",
            "source": {"name": "Synthetic Field Team", "type": "field", "source_id": "WF-FRESH"},
        },
    ]
    freshness_rules = [
        {
            "id": "recent-wildfire",
            "kinds": ["wildfire"],
            "min_severity": 0.70,
            "min_confidence": 0.60,
            "max_age_hours": 2,
        }
    ]
    freshness_input = out / "freshness-input.jsonl"
    _write_jsonl(freshness_input, freshness_events)
    rules_path = out / "freshness-rules.json"
    rules_path.write_text(json.dumps(freshness_rules, indent=2), encoding="utf-8")
    alert_text = run(
        [
            sys.executable,
            str(repos["crisisweave-alerts"] / "alerts.py"),
            str(rules_path),
            "--as-of",
            "2026-01-01T12:00:00Z",
        ],
        stdin=freshness_input.read_text(encoding="utf-8"),
    )
    freshness_alerts = _jsonl(alert_text)
    if [row.get("event_id") for row in freshness_alerts] != ["case-wildfire-fresh"]:
        raise AssertionError("freshness case must alert only on the recent report")
    _write_jsonl(out / "freshness-alerts.jsonl", freshness_alerts)

    operational = _jsonl((artifact / "worksites-operational.jsonl").read_text(encoding="utf-8"))
    public = _jsonl((artifact / "worksites.jsonl").read_text(encoding="utf-8"))
    raw_events = _jsonl((artifact / "raw.jsonl").read_text(encoding="utf-8"))
    if not operational or len(operational) != len(public):
        raise AssertionError("worksite case requires matching operational and public records")
    assigned = next((row for row in operational if row.get("state") == "assigned"), None)
    if assigned is None:
        raise AssertionError("worksite case requires an assigned operational record")
    public_by_id = {row.get("id"): row for row in public}
    public_assigned = public_by_id.get(assigned.get("id"))
    if public_assigned is None:
        raise AssertionError("assigned worksite is missing from the public projection")
    forbidden = {"assigned_team", "coordinator_instructions", "description"}
    if forbidden & set(public_assigned):
        raise AssertionError("public worksite case leaked operational-only fields")
    if {row.get("id") for row in raw_events} & {row.get("id") for row in operational}:
        raise AssertionError("hazard report IDs must not become worksite IDs")

    cases = [
        {
            "id": "fragmented-flood",
            "question": "Can multiple reports become one incident without hiding their provenance or disagreement?",
            "inputs": {"reports": 2, "independent_sources": 2},
            "result": {
                "verified_incidents": 1,
                "confidence": merged.get("confidence"),
                "severity_range": verification.get("severity_range"),
                "observation_window": verification.get("observation_window"),
                "provenance_entries": verification.get("provenance_entries"),
                "source_ids": sorted(entry.get("source_id") for entry in evidence),
            },
        },
        {
            "id": "stale-wildfire",
            "question": "Can a high-severity but old report be prevented from triggering the same alert as a recent report?",
            "inputs": {"reports": 2, "max_age_hours": 2, "as_of": "2026-01-01T12:00:00Z"},
            "result": {
                "alerted_event_ids": [row.get("event_id") for row in freshness_alerts],
                "blocked_event_ids": ["case-wildfire-stale"],
            },
        },
        {
            "id": "recovery-worksite",
            "question": "Can recovery work stay explicit and private operational details stay out of the public snapshot?",
            "inputs": {
                "hazard_reports": len(raw_events),
                "explicit_worksites": len(operational),
            },
            "result": {
                "hazard_reports_converted_to_worksites": 0,
                "assigned_operational_worksite": assigned.get("id"),
                "assigned_team_visible_operationally": bool(assigned.get("assigned_team")),
                "assigned_team_visible_publicly": "assigned_team" in public_assigned,
                "public_projection_fields_removed": sorted(forbidden),
            },
        },
    ]

    index = {
        "synthetic": True,
        "deployment_claim": "none",
        "case_count": len(cases),
        "cases": cases,
    }
    (out / "index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")

    results_md = [
        "# Reproducible case study results",
        "",
        "All three scenarios are synthetic evaluation fixtures. They do not claim a live humanitarian deployment.",
        "",
    ]
    for case in cases:
        results_md.extend(
            [
                f"## {case['id']}",
                "",
                str(case["question"]),
                "",
                "~~~json",
                json.dumps(case["result"], indent=2),
                "~~~",
                "",
            ]
        )
    (out / "RESULTS.md").write_text("\n".join(results_md), encoding="utf-8")
    return index
