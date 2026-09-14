# CrisisWeave

CrisisWeave is a public crisis-information and recovery-coordination prototype with **two deliberately different user surfaces**:

1. **Coordinator / information-management view** — turns fragmented alerts and field reports into a provenance-preserving, confidence-scored, map-ready incident stream.
2. **Volunteer work view** — shows concrete recovery worksites that were explicitly requested or assessed, including work type, crew needs, skills, status and safety notes.

The distinction is intentional. CrisisWeave must **not** infer that a household needs cleanup merely because a flood, wildfire or other hazard occurred nearby. Incident intelligence and volunteer work requests are separate data contracts.

It is built as several small repositories rather than one opaque application. The umbrella repository contains an end-to-end integrator that clones and exercises all seven public modules as one system.

## What it combines

`crisisweave-ingests` → CAP, RSS/Atom and generic JSON normalization  
`crisisweave-sim` → deterministic flood, wildfire and earthquake test reports  
`crisisweave-verify` → candidate matching, deduplication and evidence aggregation  
`crisisweave-alerts` → transparent severity/confidence/area/tag rules  
`crisisweave-map` → coordinator incident console + volunteer work board  
`crisisweave-offline` → service-worker caching and last-useful-feed fallback  
`crisisweave-docs` → architecture and threat model

The private `crisisweave-core` repository is intentionally **not** required by the public demo. Public components exchange documented JSON contracts so the public stack remains reproducible without private code.

## One-command cross-repo demo

Linux/macOS/Git Bash:

```bash
bash demo.sh
```

Windows PowerShell:

```powershell
./demo.ps1
```

Or directly:

```bash
python integrate.py --workspace ./crisisweave-demo
```

The integrator:

1. clones or updates all seven public repositories;
2. generates a deterministic multi-hazard stream;
3. creates a synthetic CAP alert and a generic JSON sensor report;
4. normalizes both through `crisisweave-ingests`;
5. combines them with simulated reports;
6. runs deterministic verification/deduplication;
7. evaluates transparent alert rules;
8. creates a separate set of explicit **synthetic recovery worksites** for the volunteer demo;
9. assembles the coordinator console, volunteer work board and offline cache into one static field package;
10. bundles the architecture and threat model beside the runnable artifact;
11. performs sanity checks and fails if required outputs or safety assumptions are violated.

The public demo uses synthetic data only.

## Run the field package

```bash
cd crisisweave-demo/artifact
python -m http.server 8765 -d web
```

### Volunteer work board

Open:

```text
http://localhost:8765/volunteer.html
```

It shows explicit worksites with:

- cleanup type
- worksite status
- urgent/high/normal/low priority
- people requested
- required skills
- safety notes
- approximate location and optional distance from the volunteer
- coordinator instructions

The volunteer view contains no survivor PII in the public demo and does not provide a fake “claim” button because the static demo has no authoritative shared assignment backend.

### Coordinator / information-management console

Open:

```text
http://localhost:8765/index.html
```

It shows:

- highest-priority incidents first
- evidence/corroboration in plain language
- official vs non-official reports
- map and list views
- search and filters
- optional distance from the user's location
- cached fallback when feeds become unavailable

Raw JSON import is still available to operators, but it is hidden from the primary volunteer workflow.

## Output

`artifact/raw.jsonl` — all normalized reports before verification  
`artifact/verified.jsonl` — merged incidents with evidence metadata  
`artifact/alerts.jsonl` — transparent alert-rule matches  
`artifact/worksites.jsonl` — explicit synthetic recovery worksites  
`artifact/summary.json` — E2E run summary  
`artifact/web/index.html` — coordinator / IM console  
`artifact/web/volunteer.html` — volunteer work board  
`artifact/docs/` — architecture + threat model

## Data contracts

Incident information uses [`schema/event.schema.json`](schema/event.schema.json).

Volunteer recovery work uses [`schema/worksite.schema.json`](schema/worksite.schema.json).

Critical rules:

1. Preserve source URLs and source identifiers.
2. Never turn absence of evidence into evidence of safety.
3. Never turn a hazard incident into a household work request without an explicit, authorised request or assessment.
4. Keep raw source material separate from normalized fields.
5. Treat confidence as an explainable ranking signal, not a probability that a report is true.
6. Prefer deterministic behavior in the critical path; ML belongs behind optional enrichment boundaries.
7. Degrade gracefully when connectivity disappears.
8. Keep official and non-official reports visibly distinguishable.
9. Minimise survivor PII and do not expose it in public feeds.

## Target users

CrisisWeave should not pretend that one interface serves everyone.

**Coordinator / IM users** need deduplication, provenance, alert triage, source visibility and a common incident picture.

**Cleanup volunteers** need concrete worksites, crew requirements, skills, status, hazards and coordinator instructions. They generally do not need to inspect CAP feeds, JSONL files or confidence decimals.

A production deployment would still need authenticated organisations, permissions, authoritative worksite assignment/synchronisation, audit logs, protected survivor information, and integrations with existing disaster-recovery systems. The current volunteer board demonstrates the interaction and data contract; it is not yet a replacement for a mature work-order platform.

## Existing open-source building blocks

The coordinator map uses MapLibre GL JS. The rest of the critical demo path intentionally uses Python's standard library so the cross-repo test can run with minimal dependencies.

The project is designed to interoperate with existing humanitarian and recovery systems rather than displace them. Real adapters can be added at the ingestion and worksite boundaries without changing the internal incident-verification contract.

## Automated integration check

The umbrella repository contains a GitHub Actions E2E workflow that runs the same cross-repository integrator. This catches interface drift between repositories instead of allowing each module to pass its own tests while the system as a whole breaks.

## Safety scope

CrisisWeave is decision-support and coordination software, not an emergency authority. It must not be used as the sole source for evacuation, medical, fire, police or rescue decisions, and the volunteer demo is not an authoritative dispatch system.

Real deployments need authenticated feeds, source governance, permissions, operational monitoring, rate limits, abuse controls, privacy protections, coordinator oversight and clear escalation procedures.

## Status and licensing

This is an early public MVP, not a production emergency platform. The repositories are publicly readable, but a formal project license has not yet been selected. Until a license is added, do not describe the code as redistributable open-source software.
