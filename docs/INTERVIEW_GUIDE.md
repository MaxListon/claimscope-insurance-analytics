# Interview preparation

## Thirty-second explanation
ClaimScope analyzes real motor insurance records with Python and SQL. It makes policy-year denominators explicit, prevents claim joins from multiplying exposure, and checks agreement between reported claim counts and recorded amounts. It combines an interactive portfolio report with uncertainty and a held-out frequency benchmark.

## Be ready to explain
1. Why 10 claims on 100 policy-years differs from 10 claims on 1,000 policy-years.
2. How aggregating claims before joining preserves the policy grain.
3. Why source amount records and reported claim counts can disagree and why you did not silently replace either.
4. Why premium is required to report a loss ratio.
5. Why whole-policy bootstrapping preserves zero-claim exposure and within-policy claims.
6. Why capping large claims is a sensitivity analysis, not a better estimate by definition.
7. Why exposure-weighted Poisson rate regression corresponds to modeling counts with an exposure offset.
8. Why a random policy split cannot establish future-year performance.
9. What changes would be required before a business could operationalize the analysis.

Use the generated memo for measured results. Describe your actual contribution accurately; do not imply manual verification against insurer systems, business deployment, or personal work you cannot explain. Rebuild the pipeline yourself and make one independently understood extension before relying on this project in an interview.

## Uncertainty discussion examples
- Explain why recorded cost of 940.26 for ages 18–24 belongs beside its 372.85–1,735.24 bootstrap interval and largest-policy share of 34.7%.
- Contrast a Poisson frequency interval with a whole-policy empirical bootstrap. Neither represents unseen future tail losses or unknown customer dependence.
- Explain why top-quartile resample share measures rank stability rather than future-risk probability.
- Show how the built wheel and its dashboard assets are verified independently of editable installation.
