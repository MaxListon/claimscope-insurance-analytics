-- One row per policy in each dimension; exposure is never joined to raw claims.
CREATE OR REPLACE TABLE segment_report AS
WITH dimensions AS (
 SELECT IDpol, Exposure, ClaimNb, recorded_claims, recorded_amount, 'Region' dimension, cast(Region AS VARCHAR) segment FROM policy_mart
 UNION ALL SELECT IDpol, Exposure, ClaimNb, recorded_claims, recorded_amount, 'Driver age',driver_band FROM policy_mart
 UNION ALL SELECT IDpol, Exposure, ClaimNb, recorded_claims, recorded_amount, 'Vehicle age',vehicle_band FROM policy_mart
 UNION ALL SELECT IDpol, Exposure, ClaimNb, recorded_claims, recorded_amount, 'Bonus / malus',bonus_band FROM policy_mart
 UNION ALL SELECT IDpol, Exposure, ClaimNb, recorded_claims, recorded_amount, 'Area',cast(Area AS VARCHAR) FROM policy_mart
 UNION ALL SELECT IDpol, Exposure, ClaimNb, recorded_claims, recorded_amount, 'Fuel',cast(VehGas AS VARCHAR) FROM policy_mart
)
SELECT dimension, segment, count(*) policies, sum(Exposure) exposure,
 sum(ClaimNb) reported_claims, sum(recorded_claims) recorded_claims,
 sum(recorded_amount) recorded_amount,
 sum(ClaimNb)/sum(Exposure) frequency,
 sum(recorded_amount)/sum(Exposure) recorded_cost_per_year,
 sum(recorded_amount)/nullif(sum(recorded_claims),0) mean_recorded_claim
FROM dimensions GROUP BY dimension, segment;
CREATE OR REPLACE TABLE reconciliation_report AS
SELECT reconciliation_status, count(*) policies,sum(Exposure) exposure,
 sum(ClaimNb) reported_claims,sum(recorded_claims) recorded_claims,
 sum(recorded_amount) recorded_amount
FROM policy_mart GROUP BY reconciliation_status;

-- Reusable age-by-region grain for standardization and population support review.
CREATE OR REPLACE TABLE region_age_cells AS
SELECT Region, driver_band, count(*) policies, sum(Exposure) exposure,
       sum(ClaimNb) reported_claims
FROM policy_mart GROUP BY Region, driver_band ORDER BY Region, driver_band;
