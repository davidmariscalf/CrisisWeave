# CrisisWeave

CrisisWeave is a public crisis-information and recovery-coordination prototype with separate surfaces for information management, volunteer work, authenticated deployment and public infrastructure.

1. **Coordinator / information-management view** — fragmented alerts and field reports become a provenance-preserving, confidence-scored, map-ready incident stream.
2. **Volunteer work view** — concrete recovery worksites that were explicitly requested or assessed, with crew needs, skills, state and safety notes.
3. **Platform boundary** — organisation identity, role-based permissions, private-data separation, audit, rate limiting and an authenticated API gateway.
4. **Infrastructure boundary** — public site, role-specific synthetic demos, security headers, health checks, deployment configuration, external-component profiles and secret-scanning guardrails.

A hazard incident must **never** become a household cleanup job merely because it occurred nearby.

## Public architecture

The E2E demo exercises **eleven public repositories**:

- `crisisweave-cores` — shared public contract/privacy/provenance checks, including public location-precision rules
- `crisisweave-ingests` — CAP, RSS/Atom and generic JSON normalization
- `crisisweave-sim` — deterministic synthetic flood, wildfire and earthquake reports
- `crisisweave-verify` — candidate matching, deduplication and evidence aggregation
- `crisisweave-alerts` — transparent alert rules
- `crisisweave-worksites` — worksite lifecycle, SQLite state, atomic team assignment, audit trail, privacy-minimised public export and partner adapters
- `crisisweave-platform` — organisations, roles, HMAC-protected expiring bearer tokens, revocation, private-data store, gateway, exact-origin CORS, rate limiting, health/readiness, verified backups and privacy-safe Prometheus metrics
- `crisisweave-map` — coordinator incident console + volunteer work board
- `crisisweave-offline` — service-worker caching, warmed map dependencies and snapshot fallback
- `crisisweave-docs` — architecture and threat model
- `crisisweave-infra` — public site, synthetic role demos, Netlify configuration, TLS/identity/secrets/DR/observability deployment profiles, uptime checks and secret scanning

The older private `crisisweave-core` repository is **not required** by the public path.

## One-command E2E demo

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

The integrator clones/updates all eleven modules, creates synthetic incident inputs, ingests and verifies them, evaluates alerts, imports explicit synthetic worksites into SQLite, performs an atomic team assignment, runs worksite/core/platform tests, creates a separate privacy-minimised public worksite snapshot, runs public contract/PII guardrails, bootstraps a synthetic organisation/coordinator, verifies that the issued raw bearer token is not persisted in SQLite, validates infrastructure profiles and reruns the infrastructure secret scanner.

## Outputs

- `artifact/raw.jsonl` — normalized reports before verification
- `artifact/verified.jsonl` — merged incidents with evidence metadata
- `artifact/alerts.jsonl` — alert-rule matches
- `artifact/worksites.db` — authoritative demo operational worksite state + audit trail
- `artifact/worksites-operational.jsonl` — internal E2E operational export, not copied into the browser package
- `artifact/worksites.jsonl` — explicit privacy-minimised public snapshot
- `artifact/platform-state/` — synthetic platform identity/private-state databases used by the E2E
- `artifact/platform/` — platform security/deployment/OpenAPI documentation and compose baseline
- `artifact/infra/` — validated public site plus identity, TLS, secrets, disaster-recovery and observability profiles
- `artifact/web/` — coordinator and volunteer browser package; it receives only the public worksite snapshot
- `artifact/docs/` — architecture + threat model
- `artifact/summary.json` — E2E summary

## Worksite privacy boundary

Direct PII is not the only public-data risk. Exact household coordinates and free-form operational instructions can also reveal sensitive information.

For non-synthetic public worksites CrisisWeave now requires an explicit approximate/area-only location policy. The public exporter:

- rounds non-synthetic Point coordinates to two decimal places
- removes `assigned_team`
- removes coordinator instructions and free-form descriptions
- removes partner source URLs/arbitrary partner metadata
- marks the record `visibility: public`
- leaves the authoritative operational database unchanged

Synthetic demo records can retain exact synthetic coordinates.

## Crisis Cleanup adapter

`crisisweave-worksites/adapters/crisis_cleanup.py` can transform an **authorised JSON export** from Crisis Cleanup into the public-safe CrisisWeave worksite contract. It intentionally excludes survivor name, address, phones and email, generalises the location and imports the item as `triaged` for coordinator review.

An upstream claim is recorded only as provenance; it does not become a CrisisWeave assignment. Staffing is marked for review rather than treated as authoritative.

This is not a live Crisis Cleanup API integration. No private API contract or credentials are assumed.

## Public evaluation site

The public project site is currently deployed at:

```text
https://crisisweave.netlify.app
```

The infrastructure source contains two deliberately synthetic, non-authoritative evaluation surfaces:

```text
https://crisisweave.netlify.app/volunteer-demo.html
https://crisisweave.netlify.app/coordinator-demo.html
```

They are designed for usability feedback without exposing operational feeds, credentials or survivor records. The volunteer demo has no self-claim action; assignments remain a coordinator-controlled operation.

The requested custom domain is `crisisweave.owns.it.com`; activation depends on the external domain registry accepting its pull request.

## Field package

```bash
cd crisisweave-demo/artifact
python -m http.server 8765 -d web
```

Coordinator console:

```text
http://localhost:8765/index.html
```

Volunteer board:

```text
http://localhost:8765/volunteer.html
```

The volunteer UI falls back to the packaged public snapshot when no operational API is available. The coordinator console rejects non-HTTP(S) source links and uses cached mapping dependencies where available when connectivity disappears.

## Operational worksite API

From the workspace root:

```bash
python crisisweave-worksites/worksites.py --db artifact/worksites.db serve --port 8787
```

The authenticated deployment boundary lives in `crisisweave-platform`. Its `openapi.yaml`, README and `artifact/platform/DEPLOYMENT.md` describe the platform API and deployment baseline.

## Platform hardening now exercised

The public platform MVP now includes:

- raw bearer tokens stored only as HMAC digests
- 24-hour CLI token expiry by default, configurable for shorter sessions
- token listing, individual revocation and principal deactivation
- exact-origin authenticated browser CORS/preflight
- actor-spoof prevention for worksite mutations
- private-record optimistic concurrency with `ETag` / `If-Match`
- graceful `502` behavior if the worksite service is unavailable
- request IDs and baseline API security headers
- online SQLite backups with integrity checks and SHA256 manifests
- a machine-readable OpenAPI contract
- an instrumented Docker server exposing private-network Prometheus metrics without user/worksite/path/token labels

## Evaluated production components

`crisisweave-infra/ecosystem/components.lock.json` pins external projects that close deployment gaps more safely than reimplementing them:

- authentik + oauth2-proxy — external OIDC/MFA boundary
- Caddy — backend TLS/reverse proxy
- OpenBao — secret/key management
- Litestream — continuous single-writer SQLite disaster recovery
- restic — encrypted snapshots and restore drills
- Prometheus + blackbox_exporter — central metrics and external HTTP/TLS probes
- rqlite — evaluated future multi-node candidate only, not adopted

These are deployment profiles, **not claims that the components are currently running**.

## Safety invariants

1. Preserve source identifiers and provenance.
2. Never turn absence of evidence into evidence of safety.
3. Never infer a household work request from hazard proximity.
4. Keep raw source material separate from normalized fields.
5. Treat confidence as an explainable ranking signal, not a probability of truth.
6. Keep official and non-official reports visibly distinguishable.
7. Do not expose direct survivor PII in public feeds.
8. Non-synthetic public worksites must generalise location and omit operational-only fields.
9. Degrade gracefully when connectivity disappears.
10. Do not allow two teams to silently claim the same worksite.
11. Do not store raw platform bearer tokens in the identity database.
12. Keep private records separate from public worksite/incident feeds.
13. Never commit deployment secrets or API credentials into public repositories.
14. Reject stale private-record writes when clients provide a version guard.
15. A public demo card is never authority to enter a property or hazardous area.

## Roles

**Coordinator / IM users** need provenance, alert triage, source visibility, worksite state and privileged coordination operations.

**Cleanup volunteers** need concrete worksites, crew requirements, skills, hazards and instructions; they do not need CAP/JSON internals or incident-confidence controls.

**Viewers** can inspect operational/intelligence surfaces without mutation privileges.

## What is still not production-ready

Much of the remaining work is now deployment/integration rather than missing repository structure. A real humanitarian deployment still needs the recommended identity/TLS/secrets/DR/monitoring components to be actually provisioned, encrypted persistent storage/KMS, an authoritative shared transactional store before multi-writer scale-out, shared rate limiting when scaled, measured recovery objectives, privacy/retention governance, organisation onboarding/offboarding, incident-response ownership and an approved live integration contract with a recovery organisation such as Crisis Cleanup.

CrisisWeave remains decision-support and coordination software, not an emergency authority. It must not be the sole source for evacuation, medical, fire, police or rescue decisions.

## Status and licensing

This is an early public MVP. The repositories are publicly readable, but a formal project-wide license has not yet been selected. Until a license is added, do not describe the full project as redistributable open-source software.
