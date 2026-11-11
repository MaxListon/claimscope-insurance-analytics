# Batch reporting runbook

## Build and review
Run the pipeline from the repository root after installing dependencies. First download is HTTPS with pinned fingerprints; cached files are rehashed on every build. Changed data require an explicit source-manifest update and review of the resulting metric changes.

The pipeline refuses a second writer using an exclusive .build.lock. A crash can leave a stale lock: first verify no ClaimScope process is running, then remove that file and rebuild. No database writer should run concurrently.

All calculations, contracts, model fitting, and report rendering complete in a temporary staging directory before artifacts replace existing files. Replacement is atomic per file, not a transactional swap of the complete artifact set. Do not serve live reports during a rebuild that requires strict snapshot consistency. For publication, commit and publish only after a complete successful build. This is a portfolio batch system, not a high-availability service.

## Failure cases
- Fingerprint mismatch: stop; do not bypass checks. Restore the pinned file or review a deliberate source version change.
- Missing source offline: perform one online build before using --offline.
- Input/SQL contract failure: inspect source and join logic. Do not remove an assertion merely to get a green build.
- Count mismatch/orphan records: recorded as source exceptions, not hidden. Review the reconciliation report.
- Changed model metrics: compare dependencies and split logic, inspect validation scores, and avoid repeatedly tuning against the fixed test results.

`reports/build_manifest.json` hashes source code, SQL, template, source metadata, dependency specification, and generated artifacts. Hashes detect changes; they do not authenticate a malicious publisher. Run tests and the artifact verifier before publishing.

## Deploy dashboard on GitHub Pages
The Pages workflow runs after the Checks workflow succeeds for a main-branch push, checks out that verified commit, and publishes docs plus aggregate reports. No Python backend, private policy data, database, or raw source is deployed. An intentional source build requires the full-data workflow; normal unit tests use fixtures. Review the workflow result before presenting a new dashboard version.

## Operational boundaries
No authentication, customer uploads, multiuser edits, streaming ingestion, underwriting, or persistent prediction service. The model supports historical exploration only. Raw source remains local and downloadable from the original host. CI uses a clean Python environment; precise dependency versions are in requirements-lock.txt for the validated environment.
