# CrisisWeave

CrisisWeave is a public crisis-information and recovery-coordination prototype with **two deliberately different user surfaces**:

1. **Coordinator / information-management view** — turns fragmented alerts and field reports into a provenance-preserving, confidence-scored, map-ready incident stream.
2. **Volunteer work view** — shows concrete recovery worksites that were explicitly requested or assessed, including work type, crew needs, skills, status and safety notes.

The distinction is intentional. CrisisWeave must **not** infer that a household needs cleanup merely because a flood, wildfire or other hazard occurred nearby.

## Public architecture

The E2E demo now exercises **nine public repositories**:

- `crisisweave-cores` — shared public contract/privacy/provenance checks
- `crisisweave-ingests` — CAP, RSS/Atom and generic JSON normalization
- `crisisweave-sim` — deterministic synthetic flood, wildfire and earthquake reports
- `crisisweave-verify` — candidate matching, deduplication and evidence aggregation
- `crisisweave-alerts` — transparent severity/confidence/area/tag rules
- `crisisweave-worksites` — worksite lifecycle, SQLite state, atomic team assignment, audit trail and localhost API
- `crisisweave-map` — coordinator incident console + volunteer work board
- `crisisweave-offline` — service-worker caching and snapshot fallback
- `crisisweave-docs` — architecture and threat model

The older private `crisisweave-core` repository is **not required** by the public path. `crisisweave-cores` is the public shared layer.

## One-command E2E demo

Linux/macOS/Git Bash:

```bash
bash demo.sh
```

Windows PowerShell:

```powershell
./demo.ps1
```

Or:

```bash
python integrate.py --workspace ./crisisweave-demo
```

The integrator clones/updates all nine public modules, creates synthetic incident inputs, ingests them, verifies/deduplicates them, evaluates alert rules, imports explicit synthetic recovery worksites into SQLite, performs an atomic demo team assignment, checks public contracts/PII guardrails, and packages the coordinator and volunteer interfaces with offline fallback.

## Run the field package

After the E2E run:

```bash
cd crisisweave-demo/artifact
python -m http.server 8765 -d web
```

Coordinator / information-management console:

```text
http://localhost:8765/index.html
```

Volunteer work board:

```text
http://localhost:8765/volunteer.html
```

The volunteer UI reads the packaged `worksites.jsonl` snapshot when no operational API is available.

### Operational worksite API

From the `crisisweave-demo` workspace root, in another terminal:

```bash
python crisisweave-worksites/worksites.py --db artifact/worksites.db serve --port 8787
```

Then open:

```text
http://localhost:8765/volunteer.html?api=http://127.0.0.1:8787/api/worksites
```

This lets the volunteer board read the SQLite-backed operational state. Write operations are intended for coordinators/API clients, not as a fake volunteer “claim” button.

## Outputs

- `artifact/raw.jsonl` — normalized reports before verification
- `artifact/verified.jsonl` — merged incidents with evidence metadata
- `artifact/alerts.jsonl` — transparent alert-rule matches
- `artifact/worksites.db` — operational SQLite worksite state + audit trail
- `artifact/worksites.jsonl` — public-safe worksite snapshot
- `artifact/summary.json` — E2E summary
- `artifact/web/index.html` — coordinator console
- `artifact/web/volunteer.html` — volunteer work board
- `artifact/docs/` — architecture + threat model

## Data contracts and safety rules

Incident information uses the umbrella event contract. The canonical recovery-work contract lives in `crisisweave-worksites/schema/worksite.schema.json`. Cross-module public guardrails live in `crisisweave-cores/contracts.py`.

Critical rules:

1. Preserve source identifiers and provenance.
2. Never turn absence of evidence into evidence of safety.
3. Never turn a hazard incident into a household work request without an explicit authorised request or assessment.
4. Keep raw source material separate from normalized fields.
5. Treat confidence as an explainable ranking signal, not a probability of truth.
6. Keep official and non-official reports visibly distinguishable.
7. Do not expose direct survivor PII in public feeds.
8. Degrade gracefully when connectivity disappears.
9. Do not allow two teams to silently claim the same worksite.

## Target users

**Coordinator / IM users** need deduplication, provenance, alert triage, source visibility and a common incident picture.

**Cleanup volunteers** need concrete worksites, crew requirements, skills, state, hazards and coordinator instructions. They generally do not need CAP files, JSONL internals or confidence decimals.

## What is still not production-ready

The public prototype now has a real local worksite state machine, atomic assignment and audit history, but production deployment would still need authenticated organisations/users, permissions, protected survivor data storage, robust multi-node synchronisation, rate limits, monitoring, backups, deployment hardening, data-retention policy, governance and real integrations with recovery organisations.

CrisisWeave is decision-support and coordination software, not an emergency authority. It must not be used as the sole source for evacuation, medical, fire, police or rescue decisions.

## Status and licensing

This is an early public MVP. The repositories are publicly readable, but a formal project-wide license has not yet been selected. Until a license is added, do not describe the full project as redistributable open-source software.
