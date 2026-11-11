# ClaimScope — portfolio review briefing

## Recommendation
Prioritize a review of large claims and exposure-adjusted segment differences. The pinned extracts reconcile exactly: preserve that control as the data change, and treat cost differences as a review shortlist rather than a pricing recommendation.

## Verified findings
- 677,991 real policy records represent 358,482.84 policy-years, with 26,444 reported claims.
- 26,444 amount records total 59,909,216.50 source monetary units. 0 records (0.00) have no policy match and are excluded from segment cost metrics, while retained in source reconciliation.
- 0 policies have different reported counts and linked amount-record counts. The two bases are disclosed separately; no fabricated records or count replacements were used.
- Portfolio frequency is 7.38 reported claims per 100 policy-years. Linked recorded cost is 167.12 per policy-year, with a 95% policy bootstrap interval [144.76, 200.72].
- The largest recorded claim is 4,075,400.56; amounts strictly above the 99th percentile contribute 38.0% of source recorded cost. Tail sensitivity is material and should accompany segment rankings.
- Joining raw claims directly to policies would inflate summed exposure by 0.283%. The SQL aggregates claim records first and preserves zero-claim policies.
- A regularized Poisson frequency benchmark changes held-out exposure-weighted deviance by 4.08% versus a constant training rate (positive means better). This is an internal random policy split, not temporal or external validation.

## Portfolio mix and model sensitivity
- Direct standardization applies the full portfolio's exposure-weighted driver-age distribution to every region. With at least 100 policy-years in every age band, 16 of 22 regions are supported, representing 97.4% of exposure. Unsupported regions remain visible; their adjusted rates are not imputed.
- The original model's improvement has a 95% paired policy-bootstrap interval of 3.63%–4.48%, conditional on the fitted model.
- Removing bonus/malus, while freezing the original split and selected regularization, leaves 1.63% improvement over baseline. Predictor availability deserves review before treating the original performance as deployable.
- The single largest amount record accounts for 6.80% of total source recorded cost. Removing it mechanically changes linked recorded cost to 155.75 per policy-year; this is an influence diagnostic, not an estimate of savings.

The age adjustment and no-bonus model are diagnostic extensions developed after the original holdout was examined. They do not establish future-period performance or a new untouched validation result. Age standardization adjusts only for measured driver-age mix. Poisson intervals assume independent cell counts; the model bootstrap excludes training and population-shift uncertainty.

## Follow-up before operational use
The current source has no unmatched records or count discrepancies. Keep these checks as future-build controls. Request policy effective dates, claim IDs, valuation dates, earned premium, and reliable currency metadata. Reconcile a sample against original source records; manual reconciliation to insurer systems is unavailable here.

No loss ratio, causal effect, profit, realized savings, or deployable insurance premium is estimated. These are historical, anonymized French motor insurance records. Some amounts use French claim settlement conventions; amounts do not necessarily measure ultimate economic loss. No timestamps support chronological backtesting.
