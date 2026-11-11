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

## Direct regional age standardization
The full portfolio reference weight for each age band is its exposure divided by all portfolio exposure. A region's standardized frequency is the sum of reference weights multiplied by its age-band frequencies. Reference weights are never renormalized around an unsupported band. The primary support rule is at least 100 policy-years in every reference band, fixed before inspecting these new results; sensitivity views use 50 and 250. Unsupported regions remain in the report and coverage denominator.

Ranks compare supported regions only. Approximate 95% intervals use variance sum(weight² × count / exposure²), independent Poisson cell counts, and a normal approximation truncated at zero. They exclude portfolio-reference uncertainty and heterogeneity. Multiple exploratory rankings are not significance tests. Age adjustment cannot remove other measured or unmeasured differences and is not a causal regional effect.

## Diagnostic extensions and model uncertainty
The no-bonus/malus sensitivity retains the original policy partitions and selected alpha, fits on training rows only, and does not select a replacement model using test performance. It was developed after the original holdout was inspected, so it is explicitly a post-holdout diagnostic. Bonus/malus timing remains unverified; removal is not proof that all remaining features were available at original underwriting.

The model improvement interval uses 400 paired policy resamples, seed 20261111. Each sampled policy carries its outcome, exposure, original prediction and baseline prediction together. Recompute relative exposure-weighted deviance improvement in each resample. This conditions on a fixed fitted model and excludes training variability, customer dependence and future-population drift.

Cumulative top-1, top-5 and top-10 amount-record influence is reported separately from the percentile scenarios. Exclude those records from linked cost while retaining all original exposure; source amount shares include all source records. Identical amounts are ordered stably and not deduplicated.

## Segment-level uncertainty and rank stability
Within each reporting segment, independently resample whole policies with replacement 400 times, retaining paired exposure, reported count and linked recorded amount. Compress identical triples into multinomial multiplicities; this is equivalent to empirical policy resampling. Batches of 25 limit temporary memory. A namespaced SHA-256 of dimension and segment defines the seed.

Each draw computes sum(count)/sum(exposure) and sum(amount)/sum(exposure). Central 95% percentile intervals condition on observed policies and fixed segment sizes. They avoid a Poisson outcome assumption but still assume independent policies and cannot represent unseen extreme losses. Repeated customers are not identifiable. Zero-claim segments have degenerate empirical frequency intervals; retain the complementary Poisson upper bound in the Segment explorer.

Cost-ranking eligibility requires at least 1,000 policy-years and 30 reported claims. In each within-dimension draw, mark the highest-cost ceil(eligible segments/4), resolving exact ties by stable segment label order. The share of draws describes rank stability, not a posterior probability, future-risk probability or causal effect. These exploratory intervals have no simultaneous-coverage guarantee.

The capped ranking uses the existing global source 99th claim-amount percentile and the same exposure. Cap individual claim records before policy aggregation. Largest-policy amount share uses combined policy amounts. Every bootstrap segment must reconcile policy count, exposure, claims, frequency and original cost with SQL reporting.
