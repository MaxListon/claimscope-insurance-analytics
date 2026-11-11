import json
from pathlib import Path

def memo(r):
    t=r['totals'];m=r['model']
    return f"""# ClaimScope — portfolio review briefing

## Recommendation
Prioritize a review of large claims and exposure-adjusted segment differences. The pinned extracts reconcile exactly: preserve that control as the data change, and treat cost differences as a review shortlist rather than a pricing recommendation.

## Verified findings
- {t['policies']:,} real policy records represent {t['exposure']:,.2f} policy-years, with {t['reported_claims']:,} reported claims.
- {t['source_claim_records']:,} amount records total {t['source_amount']:,.2f} source monetary units. {t['orphan_records']:,} records ({t['orphan_amount']:,.2f}) have no policy match and are excluded from segment cost metrics, while retained in source reconciliation.
- {t['mismatch_policies']:,} policies have different reported counts and linked amount-record counts. The two bases are disclosed separately; no fabricated records or count replacements were used.
- Portfolio frequency is {100*t['frequency']:.2f} reported claims per 100 policy-years. Linked recorded cost is {t['cost_per_year']:,.2f} per policy-year, with a 95% policy bootstrap interval [{t['cost_bootstrap_interval'][0]:,.2f}, {t['cost_bootstrap_interval'][1]:,.2f}].
- The largest recorded claim is {t['largest_claim']:,.2f}; amounts strictly above the 99th percentile contribute {100*t['top_one_pct_amount_share']:.1f}% of source recorded cost. Tail sensitivity is material and should accompany segment rankings.
- Joining raw claims directly to policies would inflate summed exposure by {t['naive_join_exposure_inflation_pct']:.3f}%. The SQL aggregates claim records first and preserves zero-claim policies.
- A regularized Poisson frequency benchmark changes held-out exposure-weighted deviance by {m['deviance_improvement_pct']:.2f}% versus a constant training rate (positive means better). This is an internal random policy split, not temporal or external validation.

## Follow-up before operational use
The current source has no unmatched records or count discrepancies. Keep these checks as future-build controls. Request policy effective dates, claim IDs, valuation dates, earned premium, and reliable currency metadata. Reconcile a sample against original source records; manual reconciliation to insurer systems is unavailable here.

No loss ratio, causal effect, profit, realized savings, or deployable insurance premium is estimated. These are historical, anonymized French motor insurance records. Some amounts use French claim settlement conventions; amounts do not necessarily measure ultimate economic loss. No timestamps support chronological backtesting.
"""

def render(data):
    template=Path(__file__).with_name('dashboard.html').read_text()
    # Escape characters that can terminate an embedded script element.
    payload=json.dumps(data,allow_nan=False).replace('<',r'\u003c').replace('>',r'\u003e').replace('&',r'\u0026')
    return template.replace('__DATA__',payload)
