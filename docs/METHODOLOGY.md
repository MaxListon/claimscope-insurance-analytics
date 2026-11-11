# Methodology and decisions

## Population and grain
Each freMTPL2freq row is a policy. IDpol is an identifier, never a predictor. Each freMTPL2sev row is a recorded claim amount; there is no claim ID or event date. Retain identical-looking rows because sameness is not proof of duplication. The pinned revision, rather than the frequently reproduced OpenML release, defines this build's population.

Policies are retained regardless of whether they have a claim. Positive exposures above one year are retained and counted in the quality report; clipping would alter both rates and denominator integrity. No source rows are fabricated.

## Metrics
| Metric | Numerator | Denominator |
|---|---|---|
| Frequency | Reported policy ClaimNb | Sum Exposure, in policy-years |
| Recorded cost / year | Linked amount-record sum | All matched policy exposure, including zero claims |
| Mean recorded claim | Linked amount-record sum | Number of linked amount records |
| Loss ratio | Unavailable | Premium unavailable |

The cost rate is not labeled an actuarially validated pure premium: inconsistent extracts and unknown valuation conventions limit that interpretation. Amount units are preserved without currency conversion or inflation adjustment.

## Reconciliation
Group the amount table by policy, then LEFT JOIN policies. Unmatched amount records are separately retained. Check that matched + unmatched records and amounts equal the original amount source. Every segment dimension must reconcile policy count, exposure, reported counts, linked counts and linked amount. Count discrepancies are warnings disclosed in a separate report, not repaired by replacing ClaimNb.

## Intervals
Frequency intervals are exact central 95% Poisson intervals. They assume independent Poisson events; unmeasured heterogeneity, repeated underlying customers, and overdispersion can invalidate nominal coverage. The interval is descriptive, not a claim about protected groups or causation.

Cost intervals resample whole policies with replacement 400 times, seed 20261110, preserving each policy's paired exposure and all its linked claim amounts. Grouping identical (exposure, amount) pairs and sampling multiplicities is algebraically equivalent to a policy bootstrap, not sampling only claimants. Rare losses make intervals unstable and the empirical bootstrap cannot invent unseen tail losses.

Sensitivity compares original cost with each source amount capped at the source 99th percentile, exclusion of records strictly above it, and a count-aligned policy subset. Exposure is held fixed in the first three views. The aligned view changes the population and must not be interpreted as a corrected estimate for all policies. The percentile uses all source amount records, including orphans; application of each cost scenario uses linked records only.

## Frequency benchmark
SHA-256 of a namespaced ID maps policies to roughly 60/20/20 train/validation/test. This is a reproducible random-style policy split, not chronological validation. Related drivers/vehicles may appear under multiple policy IDs; no reliable grouping variable is available.

Fit annual rate = ClaimNb / Exposure with Exposure as sample weight. For a log-link Poisson model this yields the same coefficient estimation objective as a count model with log-exposure offset, up to constants and regularization convention. Report exposure-weighted deviance of rates. It is not per-policy count deviance, and absolute values are not comparable to benchmarks using a different scale.

Categorical bands are defined in SQL before analysis. Fit one-hot categories on training rows only. Unknown categories are ignored by the encoder. Compare alpha 0.001, 0.01, 0.1 using validation deviance. Freeze the selected model without refitting and evaluate the test partition against a constant training frequency. Decile calibration is descriptive; risk deciles are formed within the holdout. No timing metadata proves all predictors were available at original underwriting, especially bonus/malus.

The dashboard exposes benchmark limitations and a baseline comparison. There is no scoring API, pricing decision, or fairness certification.
