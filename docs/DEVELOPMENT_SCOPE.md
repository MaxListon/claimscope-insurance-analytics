# Six-week development scope

This is a realistic learning and independent development schedule, not a claim that the repository took six weeks to produce. The implementation in this repository is already built; use the schedule to reproduce, review, and extend it.

| Week | Work | Reviewable evidence |
|---|---|---|
| 1 | Understand source populations, licenses, metric requirements | Dictionary, grain diagram, denominator definitions |
| 2 | Build ingestion, policy/claim SQL marts, exception reporting | Join tests, source totals, orphan reconciliation |
| 3 | Segment frequency and cost; quantify uncertainty | Exposure-aware report, bootstrap, tail sensitivity |
| 4 | Implement a frequency baseline and regularized benchmark | Frozen split specification, validation and test results |
| 5 | Build dashboard and executive narrative | Interactive report, CSV export, decision memo |
| 6 | Reproduce in a clean environment, review limitations, add an independent extension | Passing CI, review notes, documented extension |

Useful personal extension: compare the current Poisson intervals against a policy-bootstrap frequency interval for a few prespecified segments. Explain any divergence without selecting segments based only on extreme results. The repository now includes age-standardized regional comparisons. An additional extension could investigate whether these rankings remain stable after a prespecified vehicle-age adjustment, with explicit overlap and exposure requirements.
