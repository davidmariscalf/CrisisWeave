# CrisisWeave licensing audit

This is an engineering inventory to support a project-license decision. It is not legal advice.

## Scope

The audit covers the umbrella repository plus the eleven repositories used by the locked CrisisWeave release:

- CrisisWeave
- crisisweave-cores
- crisisweave-ingests
- crisisweave-verify
- crisisweave-alerts
- crisisweave-worksites
- crisisweave-platform
- crisisweave-map
- crisisweave-offline
- crisisweave-sim
- crisisweave-docs
- crisisweave-infra

At the time of this audit, none of those repositories has a root `LICENSE` file. CrisisWeave therefore remains publicly readable source, not software with an explicit project-wide redistribution grant.

## Original CrisisWeave code

The public repositories are structured as CrisisWeave-owned application, documentation, tests and deployment configuration. Repository searches did not identify copied third-party source headers or SPDX declarations inside the CrisisWeave codebase.

That finding is an engineering signal, not proof of copyright ownership. Before selecting a license, the project owner should confirm that any externally contributed material was submitted with permission to relicense under the chosen project license.

## Bundled third-party runtime: MapLibre GL JS

The locked field-package build downloads the exact pinned MapLibre GL JS npm tarball and extracts only:

- `maplibre-gl.js`
- `maplibre-gl.css`
- the upstream `LICENSE.txt`, renamed `MAPLIBRE_LICENSE.txt`

The tarball SHA-512 is verified before extraction.

MapLibre GL JS is distributed under the BSD 3-Clause license. Redistribution requires preservation of its copyright/license notices. The CrisisWeave release path already carries the upstream license beside the packaged runtime.

This means the MapLibre runtime should remain clearly separated as third-party material and its notice must stay in distributed field packages regardless of the license selected for original CrisisWeave code.

## External deployment components

`crisisweave-infra/ecosystem/components.lock.json` references external projects such as authentik, oauth2-proxy, Caddy, OpenBao, Litestream, restic, Prometheus and blackbox_exporter.

The repository policy explicitly treats these as external integrations/deployment components and does not vendor their upstream source code into CrisisWeave. Their licenses therefore do not become the license for original CrisisWeave code, but operators must comply with each component's own license when deploying it.

The Crisis Cleanup integration is an adapter/reference boundary. CrisisWeave does not copy upstream Crisis Cleanup source code or assume private API credentials.

## CI-only tooling

The release workflow uses GitHub Actions and a pinned Playwright/Chromium test runtime to verify browser behavior. Those tools are CI dependencies and are not shipped as CrisisWeave application source or runtime assets in the sealed field package.

## Project-license decision still required

The current engineering audit did not find a bundled dependency that appears to force CrisisWeave to choose one specific permissive license for its original code.

Two previously discussed options remain reasonable candidates:

- **MIT** — short and permissive.
- **Apache License 2.0** — permissive and includes an explicit patent grant and patent-termination terms.

The project owner must choose deliberately. Do not add a project-wide `LICENSE` or describe CrisisWeave as redistributable open-source software until that decision is made.

## After the decision

Once the project license is selected:

1. Add the chosen `LICENSE` consistently to the original-code repositories.
2. Keep `MAPLIBRE_LICENSE.txt` in generated field packages and any other required third-party notices.
3. Add a top-level third-party notices document if additional vendored assets are introduced later.
4. Update README/status wording from publicly readable/public source to the selected open-source license.
5. Add CI guardrails that fail if the project license or required bundled notices disappear.
