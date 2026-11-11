# Verification record

- Clean virtual environment installed from requirements-lock.txt; dependency check passed.
- Fresh source download with no raw cache or warehouse reproduced analysis.json within relative/absolute numeric tolerance 1e-9. Minor DuckDB floating-point summation differences occur across runs; displayed results and model scores agree.
- Full real-data build passed 12 input/SQL contracts for 677,991 policies and 26,444 claim amount records.
- 23 regression tests passed, including zero-claim retention, orphan reconciliation, exposure conservation, invalid data rejection, source fingerprint rejection, lock cleanup, and holdout outcome isolation.
- Browser review covered narrow and desktop layouts, segment and metric controls, model results, and CSV export. A 20,000-policy-year region filter exported exactly six eligible rows.
- Source, SQL, template and output integrity verified against the generated build manifest.

These are local verification results. GitHub Actions results are separate evidence; CI is not described as passed until its run completes. No insurer-system reconciliation, business-user acceptance, future-period validation, or production underwriting deployment has been performed.

## Cloud verification follow-up

The first Linux reproduction exposed nondeterministic ordering of grouped reconciliation checks. The checks themselves passed, but their sequence differed from the committed JSON. The reporting query now explicitly orders dimensions, and the regression suite requires a stable order. Full data reproduction runs on every push as well as manual dispatch.

## Portfolio review edition (v1.1)

- Added direct age standardization using the full portfolio exposure mix, with explicit 50/100/250-policy-year population-support sensitivity. The primary rule supports 16 of 22 regions and 97.4% of exposure.
- Added a fixed-split, fixed-alpha model sensitivity without bonus/malus, and 400 paired policy-bootstrap resamples for original model improvement.
- Extended the suite to 30 tests, including a deliberately reversed crude/adjusted ranking example and missing-stratum rejection. Thirteen runtime contracts now reconcile the region-age reporting grain too.
- Added keyboard-accessible tabs, an executive summary, regional comparison views and model dependency reporting.
- Added dashboard script syntax checks and a deployment gate: the dashboard publishes the checked main-branch commit only after the complete Checks workflow succeeds.
- Artifact verification now compares the published report copies as well as their source outputs and raises explicit exceptions even when Python assertions are disabled.

The original test partition had already been inspected before these diagnostic extensions. No new untouched-test or future-period validation claim is made.
