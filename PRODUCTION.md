# Production readiness

CrisisWeave has two distinct meanings of "production ready": repository/release readiness and real humanitarian operational readiness. They are not the same claim.

## Reproducible release path

Use the locked component path for any release candidate:

```bash
python production_check.py
python run_pinned.py --workspace ./crisisweave-demo
python seal_artifact.py ./crisisweave-demo/artifact --lock components.lock.json
```

Or use `demo.sh` / `demo.ps1`, which run the same production path.

`integrate.py` intentionally follows component default branches and is therefore a development/update path. It must not be used to build a release artifact.

A release candidate is acceptable only when:

1. `production_check.py` passes.
2. The fast `Quality gate` passes on Python 3.11 and 3.12.
3. `Cross-repo E2E` passes against all revisions in `components.lock.json`.
4. `MANIFEST.sha256` and `BUILD_PROVENANCE.json` are present, the provenance file is itself covered by the manifest, and `seal_artifact.py --verify` passes.
5. All external GitHub Actions remain pinned to immutable 40-character commit SHAs.

## Public deployment boundary

The Netlify site is a public evaluation surface. It is suitable for synthetic demonstrations and usability evaluation; publishing that site does not mean the operational platform, identity provider, secrets manager, disaster recovery stack, monitoring stack or persistent production data plane are provisioned.

A real operational deployment additionally requires the deployment profiles documented in `crisisweave-infra` and `crisisweave-platform` to be provisioned and verified in the target environment, including identity/MFA, TLS, secrets/key management, encrypted persistent storage, backups and restore drills, observability, retention/privacy governance and incident-response ownership.

Do not describe CrisisWeave as an emergency authority, dispatch system or sole source for evacuation, medical, fire, police or rescue decisions.

## Release discipline

Do not advance `components.lock.json` merely because component default branches changed. Promote component revisions only after their own tests are green and the umbrella E2E passes at the exact proposed SHAs.

The lock file is the release bill of materials for the public CrisisWeave component set. Generated artifacts are sealed separately so that their file contents can be verified independently of Git history.
