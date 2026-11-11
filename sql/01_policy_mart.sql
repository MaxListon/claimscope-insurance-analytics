-- Claim records have no claim identifier: preserve every source row.
-- Aggregate BEFORE joining to avoid multiplying policy exposure.
CREATE OR REPLACE TABLE claim_totals AS
SELECT IDpol, count(*) AS recorded_claims, sum(ClaimAmount) AS recorded_amount
FROM claims GROUP BY IDpol;
CREATE OR REPLACE TABLE policy_mart AS
SELECT p.*, coalesce(c.recorded_claims,0) AS recorded_claims,
 coalesce(c.recorded_amount,0) AS recorded_amount,
 CASE WHEN p.ClaimNb = coalesce(c.recorded_claims,0) THEN 'Aligned'
      WHEN coalesce(c.recorded_claims,0)>p.ClaimNb THEN 'More amount records'
      ELSE 'Fewer amount records' END AS reconciliation_status,
 CASE WHEN DrivAge<25 THEN '18–24' WHEN DrivAge<35 THEN '25–34'
      WHEN DrivAge<50 THEN '35–49' WHEN DrivAge<65 THEN '50–64' ELSE '65+' END AS driver_band,
 CASE WHEN VehAge<3 THEN '0–2' WHEN VehAge<8 THEN '3–7'
      WHEN VehAge<15 THEN '8–14' ELSE '15+' END AS vehicle_band,
 CASE WHEN BonusMalus=50 THEN '50 (maximum bonus)' WHEN BonusMalus<=100 THEN '51–100' ELSE '101+' END AS bonus_band
FROM policies p LEFT JOIN claim_totals c USING(IDpol);
CREATE OR REPLACE TABLE orphan_claims AS
SELECT c.* FROM claims c ANTI JOIN policies p USING(IDpol);
