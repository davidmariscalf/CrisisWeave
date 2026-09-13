# CrisisWeave

CrisisWeave is a public crisis-information fabric for turning fragmented public alerts and field reports into a single, confidence-scored, map-ready event stream that still works when connectivity is poor.

## The real problem

During floods, fires, earthquakes, storms and other fast-moving incidents, useful information is fragmented across CAP feeds, RSS/Atom feeds, agency JSON APIs, volunteer reports and local dashboards. The hard part is not drawing another map. It is deciding whether two reports describe the same event, preserving provenance, estimating confidence, and keeping a useful view available when the network is unreliable.

CrisisWeave is designed around this pipeline:

`sources -> normalize -> verify/deduplicate -> score -> map -> offline cache -> alerts`

## Repositories

- `crisisweave-ingests`: adapters for CAP, RSS/Atom and JSON feeds.
- `crisisweave-verify`: deterministic evidence aggregation, deduplication and confidence scoring.
- `crisisweave-map`: lightweight MapLibre viewer for the normalized event stream.
- `crisisweave-offline`: service worker and offline event cache utilities.
- `crisisweave-alerts`: transparent rule-based alert engine.
- `crisisweave-sim`: deterministic synthetic incident generator for testing.
- `crisisweave-docs`: architecture, threat model and integration notes.
- `crisisweave-core`: orchestration/API service. The public event contract lives here in the umbrella repository so public modules do not depend on private code.

## Fastest way to try it

Linux/macOS/Git Bash:

```bash
bash demo.sh
```

Windows PowerShell:

```powershell
./demo.ps1
```

The scripts clone the public simulator, verifier and alert-engine repositories, generate 30 deterministic synthetic reports, merge likely duplicates and evaluate example rules. No Python packages need to be installed beyond Python itself.

## Shared contract

Every component exchanges the same JSON event shape in [`schema/event.schema.json`](schema/event.schema.json). Important design rules:

1. Preserve source URLs and source identifiers.
2. Never turn absence of evidence into evidence of safety.
3. Keep raw source text separate from normalized fields.
4. Treat confidence as an explainable score, not a claim of truth.
5. Prefer deterministic behavior in the critical path; ML can be an optional enrichment layer.
6. Degrade gracefully offline.

## Open-source building blocks

CrisisWeave deliberately reuses mature open-source ideas instead of reimplementing everything: MapLibre GL JS for mapping, FastAPI/Pydantic-style API contracts, RapidFuzz-style lexical similarity for candidate matching, H3-style spatial bucketing for scalable geospatial joins, and service-worker patterns for offline operation. CrisisWeave integration code is written specifically for this project rather than copied from those projects.

## MVP flow

1. Run `crisisweave-sim` to generate a repeatable synthetic incident stream.
2. Normalize external feeds with `crisisweave-ingests`.
3. Pipe events through `crisisweave-verify`.
4. Load the resulting JSON/JSONL in `crisisweave-map`.
5. Add `crisisweave-offline` to cache the app shell and last useful event snapshot.
6. Evaluate alert rules with `crisisweave-alerts`.

## Safety scope

CrisisWeave is decision-support software, not an emergency authority. It should not be used as the sole source for evacuation, medical, fire, police or rescue decisions. Deployments should clearly distinguish official alerts from community or machine-generated reports.

## Status

Early public MVP. Interfaces are intentionally small so individual modules can be tested independently before deeper orchestration is added. A formal project license has not yet been selected, so the source is public but should not be described as redistributable open-source software until a license is added.
