# Security Policy

CrisisWeave spans public crisis information, operator-only state, offline caches and deployment infrastructure. Security reports should preserve the same public/private boundary the product is designed to enforce.

## Reporting a vulnerability

Do not post credentials, personal data, private locations, coordinator instructions, exploit details or other sensitive evidence in a public issue.

Use GitHub private vulnerability reporting on the affected repository when available. Otherwise contact the repository owner through GitHub before public disclosure so a private reporting channel can be arranged.

Identify the affected component and exact revision whenever possible. Use synthetic fixtures for reproductions.

## High-priority areas

- public/private data-boundary failures
- authentication or authorization bypasses
- fabricated freshness, provenance or verification state
- unsafe offline caching of sensitive responses
- alerting or worksite logic that can turn unreviewed information into operational instructions
- secret leakage, mutable production sources or go-live gate bypasses
- backup, restore or audit-integrity failures
- dependency and CI/CD supply-chain compromise

## Safe testing

Do not test against real survivors, volunteers, emergency operations or third-party services without explicit authorization. Do not create load, alerts or operational work in a live organisation merely to demonstrate an issue.

## Release boundary

A green locked release is suitable for synthetic/public evaluation. Sensitive operational deployment additionally requires the operator-owned controls documented in `crisisweave-docs` and enforced where possible by `crisisweave-infra`.
