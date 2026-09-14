# CrisisWeave

CrisisWeave is a public crisis-information and recovery-coordination prototype with separate surfaces for information management, volunteer work, authenticated deployment and public infrastructure.

1. **Coordinator / information-management view** — fragmented alerts and field reports become a provenance-preserving, confidence-scored, map-ready incident stream.
2. **Volunteer work view** — concrete recovery worksites that were explicitly requested or assessed, with crew needs, skills, state and safety notes.
3. **Platform boundary** — organisation identity, role-based permissions, private-data separation, audit, rate limiting and an authenticated API gateway.
4. **Infrastructure boundary** — public site, security headers, health checks, deployment configuration and secret-scanning guardrails.

A hazard incident must **never** become a household cleanup job merely because it occurred nearby.

## Public architecture

The E2E demo now exercises **eleven public repositories**:

- `crisisweave-cores` — shared public contract/privacy/provenance checks
- `crisisweave-ingests` — CAP, RSS/Atom and generic JSON normalization
- `crisisweave-sim` — deterministic synthetic flood, wildfire and earthquake reports
- `crisisweave-verify` — candidate matching, deduplication and evidence aggregation
- `crisisweave-alerts` — transparent alert rules
- `crisisweave-worksites` — worksite lifecycle, SQLite state, atomic team assignment, audit trail and API
- `crisisweave-platform` — organisations, roles, HMAC-protected bearer tokens, private-data store, gateway, rate limiting, health/readiness, backups and deployment baseline
- `crisisweave-map` — coordinator incident console + volunteer work board
- `crisisweave-offline` — service-worker caching, warmed map dependencies and snapshot fallback
- `crisisweave-docs` — architecture and threat model
- `crisisweave-infra` — public site, Netlify configuration, deploy-safe security headers, health endpoint, uptime checks and secret scanning

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

The integrator clones/updates all eleven modules, creates synthetic incident inputs, ingests and verifies them, evaluates alerts, imports explicit synthetic worksites into SQLite, performs an atomic team assignment, runs public contract/PII guardrails, executes the platform HTTP/RBAC tests, bootstraps a synthetic organisation/coordinator, verifies that the issued raw bearer token is not persisted in SQLite, validates infrastructure files and reruns the infrastructure secret scanner.

## Outputs

- `artifact/raw.jsonl` — normalized reports before verification
- `artifact/verified.jsonl` — merged incidents with evidence metadata
- `artifact/alerts.jsonl` — alert-rule matches
- `artifact/worksites.db` — operational worksite state + audit trail
- `artifact/worksites.jsonl` — public-safe worksite snapshot
- `artifact/platform-state/` — synthetic platform identity/private-state databases used by the E2E
- `artifact/platform/` — platform security/deployment documentation and compose baseline
- `artifact/infra/` — validated public-site and deployment configuration bundle
- `artifact/web/` — coordinator and volunteer browser package
- `artifact/docs/` — architecture + threat model
- `artifact/summary.json` — E2E summary

## Public site

The public project site is currently deployed at:

```text
https://crisisweave.netlify.app
```

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

The volunteer UI falls back to the packaged snapshot when no operational API is available. The coordinator console rejects non-HTTP(S) source links and uses a local no-basemap style when launched offline after its dependencies have been cached.

## Operational worksite API

From the workspace root:

```bash
python crisisweave-worksites/worksites.py --db artifact/worksites.db serve --port 8787
```

The authenticated deployment boundary lives in `crisisweave-platform`. Its README and `artifact/platform/DEPLOYMENT.md` describe the platform API and deployment baseline.

## Safety invariants

1. Preserve source identifiers and provenance.
2. Never turn absence of evidence into evidence of safety.
3. Never infer a household work request from hazard proximity.
4. Keep raw source material separate from normalized fields.
5. Treat confidence as an explainable ranking signal, not a probability of truth.
6. Keep official and non-official reports visibly distinguishable.
7. Do not expose direct survivor PII in public feeds.
8. Degrade gracefully when connectivity disappears.
9. Do not allow two teams to silently claim the same worksite.
10. Do not store raw platform bearer tokens in the identity database.
11. Keep private records separate from public worksite/incident feeds.
12. Never commit deployment secrets or API credentials into public repositories.

## Roles

**Coordinator / IM users** need provenance, alert triage, source visibility, worksite state and privileged coordination operations.

**Cleanup volunteers** need concrete worksites, crew requirements, skills, hazards and instructions; they do not need CAP/JSON internals or incident-confidence controls.

**Viewers** can inspect operational/intelligence surfaces without mutation privileges.

## What is still not production-ready

The prototype now includes local organisation identity, RBAC, token hashing, private-data separation, audit, backups, rate limiting, deployment configuration, a public TLS-hosted static site, security headers and automated public-site health checks. A real humanitarian deployment still needs external identity/MFA, production backend TLS and managed secret storage, managed encrypted storage, robust multi-node synchronisation, shared rate limiting when scaled, central monitoring, tested disaster recovery, privacy/retention governance, organisation onboarding/offboarding, and integrations with authoritative recovery systems.

CrisisWeave remains decision-support and coordination software, not an emergency authority. It must not be the sole source for evacuation, medical, fire, police or rescue decisions.

## Status and licensing

This is an early public MVP. The repositories are publicly readable, but a formal project-wide license has not yet been selected. Until a license is added, do not describe the full project as redistributable open-source software.
