# Data dictionary

The authoritative schema is the pinned CASdatasets source; these are the fields used here.

| Field | Meaning / treatment |
|---|---|
| IDpol | Policy identifier; convert categorical labels to strings, not category codes |
| ClaimNb | Source reported claim count; nonnegative integer |
| Exposure | Positive observation exposure, in years; retain >1 |
| ClaimAmount | Positive recorded amount; retain each source row |
| DrivAge | Driver age, years; SQL bands 18–24, 25–34, 35–49, 50–64, 65+ |
| VehAge | Vehicle age, years; bands 0–2, 3–7, 8–14, 15+ |
| VehPower | Ordered source power category; categorical predictor |
| BonusMalus | Source bonus/malus; bands 50, 51–100, >100 |
| VehBrand | Anonymized vehicle brand category; retained in warehouse |
| VehGas | Fuel category |
| Area | Source density-area category A–F |
| Density | Local inhabitants per square kilometer; retained in warehouse |
| Region | Historical French region labels; preserve source labels |
| recorded_claims | Count of linked amount records, not an overwritten ClaimNb |
| recorded_amount | Sum of linked amount records; zero if no match |
| reconciliation_status | Aligned / more amount records / fewer amount records |

Warehouse tables: policies, claims, claim_totals, policy_mart, orphan_claims, segment_report, reconciliation_report. Segment_report contains six independent aggregations of the same population; summing across dimensions would multiply totals by six.
