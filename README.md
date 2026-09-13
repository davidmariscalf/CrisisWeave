# CrisisWeave

CrisisWeave is a public crisis-information fabric that turns fragmented alerts and field reports into one provenance-preserving, confidence-scored, map-ready stream that can remain useful when connectivity is poor.

It is deliberately built as several small repositories rather than one opaque application. The umbrella repository now contains an end-to-end integrator that clones and exercises all seven public modules as one system.

## What it combines

`crisisweave-ingests` → CAP, RSS/Atom and generic JSON normalization  
`crisisweave-sim` → deterministic flood, wildfire and earthquake test reports  
`crisisweave-verify` → candidate matching, deduplication and evidence aggregation  
`crisisweave-alerts` → transparent severity/confidence/area/tag rules  
`crisisweave-map` → MapLibre browser console for mapped incidents  
`crisisweave-offline` → service-worker caching and last-useful-feed fallback  
`crisisweave-docs` → architecture and threat model

The private `crisisweave-core` repository is intentionally **not** required by the public demo. Public components exchange a shared JSON event contract so the public stack remains reproducible without private code.

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
8. assembles `crisisweave-map` + `crisisweave-offline` into a static field console;
9. bundles the architecture and threat model beside the runnable artifact;
10. performs sanity checks and fails if the pipeline produces impossible counts, no CAP event, no alert, or no map-ready geometry.

The demo uses synthetic data only.

## Output

`artifact/raw.jsonl` — all normalized reports before verification  
`artifact/verified.jsonl` — merged incidents with evidence metadata  
`artifact/alerts.jsonl` — rule matches  
`artifact/summary.json` — E2E run summary  
`artifact/web/` — map + service worker + verified feed  
`artifact/docs/` — architecture + threat model

To inspect the generated field console:

```bash
cd crisisweave-demo/artifact
python -m http.server 8765 -d web
```

Then open:

`http://localhost:8765/index.html?feed=verified.jsonl`

## Shared contract

Every component exchanges the same event shape in [`schema/event.schema.json`](schema/event.schema.json). Critical design rules:

1. Preserve source URLs and source identifiers.
2. Never turn absence of evidence into evidence of safety.
3. Keep raw source material separate from normalized fields.
4. Treat confidence as an explainable ranking signal, not a probability that a report is true.
5. Prefer deterministic behavior in the critical path; ML belongs behind optional enrichment boundaries.
6. Degrade gracefully when connectivity disappears.
7. Keep official and non-official reports visibly distinguishable.

## Existing open-source building blocks

The current browser map directly uses MapLibre GL JS. The rest of the critical demo path intentionally uses Python's standard library so the cross-repo test can run with minimal dependencies. Future adapters can add H3-style spatial indexing, FastAPI services, richer fuzzy matching, routing and tile pipelines without making those dependencies mandatory for the baseline verifier.

## Automated integration check

The umbrella repository contains a GitHub Actions E2E workflow that runs the same cross-repository integrator. This catches interface drift between repositories instead of allowing each module to pass its own tests while the system as a whole breaks.

## Safety scope

CrisisWeave is decision-support software, not an emergency authority. It must not be used as the sole source for evacuation, medical, fire, police or rescue decisions. Real deployments need authenticated feeds where available, source governance, operational monitoring, rate limits, abuse controls and clear escalation procedures.

## Status and licensing

This is an early public MVP, not a production emergency platform. The repositories are publicly readable, but a formal project license has not yet been selected. Until a license is added, do not describe the code as redistributable open-source software.
