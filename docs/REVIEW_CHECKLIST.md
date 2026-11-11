# Release review checklist

## Analyst acceptance criteria
- Verify source fingerprints and policy/claim totals, then inspect every exception category.
- Confirm that every segmentation dimension and region-age table conserves policy count, exposure and claims.
- Review large-record influence before using mean cost to prioritize a segment.
- Report standardized-region coverage alongside rates; unsupported regions must remain visible.
- Compare model performance against the constant-rate baseline and the no-bonus/malus sensitivity. Preserve the original split and selection protocol.
- Read the limitations before interpreting rankings, confidence intervals or model improvements.

## Technical acceptance criteria
- Full source rebuild and all regression tests pass on GitHub, including Python 3.12 and 3.14.
- Artifact fingerprints match generated reports and dashboard.
- Inspect desktop and narrow layouts, keyboard tabs, all filter states, CSV export, and download links.
- Publish only the checked commit; verify that the live HTML equals the committed dashboard.

## Evidence still needed for business use
An independent stakeholder review, original-system record reconciliation, valuation metadata, available-at-decision-time predictors, and a genuinely later-period evaluation. These cannot be manufactured from the public files. This checklist defines review expectations; it is not a claim that external acceptance occurred.
