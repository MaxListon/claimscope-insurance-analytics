"""Data contracts fail the build; source discrepancies are separately disclosed."""
import math

def validate_inputs(policies,claims):
    errors=[]
    for name,frame in [('policies',policies),('claims',claims)]:
        if frame.isna().any().any(): errors.append(f'{name}: missing values')
        if len(frame)==0: errors.append(f'{name}: empty input')
    if policies.IDpol.astype(str).duplicated().any(): errors.append('duplicate policy identifiers')
    for name,frame in [('policies',policies),('claims',claims)]:
        ids=frame.IDpol.astype(str)
        if ids.str.strip().eq('').any() or ids.ne(ids.str.strip()).any():
            errors.append(f'{name}: blank or padded policy identifier')
    if (policies.Exposure<=0).any(): errors.append('nonpositive exposure')
    if ((policies.ClaimNb<0)|(policies.ClaimNb%1!=0)).any(): errors.append('invalid claim count')
    if (claims.ClaimAmount<=0).any(): errors.append('nonpositive claim amount')
    for frame,columns in [(policies,['Exposure','ClaimNb','DrivAge','VehAge','BonusMalus','Density','VehPower']), (claims,['ClaimAmount'])]:
        for column in columns:
            if not frame[column].map(lambda v: math.isfinite(float(v))).all(): errors.append(f'nonfinite {column}')
    if errors: raise ValueError('; '.join(errors))
    return [{'check':'Input contracts','status':'PASS','detail':'Unique policy IDs; complete, finite fields; valid counts, exposure and amounts.'}]

def validate_warehouse(con):
    checks=[]
    def check(name,ok,detail):
        checks.append({'check':name,'status':'PASS' if ok else 'FAIL','detail':detail})
        if not ok: raise ValueError(f'{name}: {detail}')
    p=con.execute('SELECT count(*),sum(Exposure),sum(ClaimNb) FROM policies').fetchone()
    m=con.execute('SELECT count(*),sum(Exposure),sum(ClaimNb) FROM policy_mart').fetchone()
    for i,label in enumerate(['Policy grain','Exposure conservation','Reported count conservation']):
        check(label,math.isclose(p[i],m[i],rel_tol=1e-10),'Raw policy total equals policy mart total')
    a=con.execute('SELECT count(*),sum(ClaimAmount) FROM claims').fetchone()
    b=con.execute('SELECT sum(recorded_claims),sum(recorded_amount) FROM policy_mart').fetchone()
    o=con.execute('SELECT count(*),coalesce(sum(ClaimAmount),0) FROM orphan_claims').fetchone()
    for i,label in enumerate(['Claim record conservation','Recorded amount conservation']):
        check(label,math.isclose(a[i],b[i]+o[i],rel_tol=1e-10),'Matched + orphan amounts/records equal source')
    for row in con.execute('SELECT dimension,sum(policies),sum(exposure),sum(reported_claims),sum(recorded_claims),sum(recorded_amount) FROM segment_report GROUP BY dimension ORDER BY dimension').fetchall():
        expected=[m[0],m[1],m[2],b[0],b[1]]
        check(f'Segment reconciliation: {row[0]}',all(math.isclose(x,y,rel_tol=1e-9) for x,y in zip(row[1:],expected)),'Every dimension reconciles all five base totals')
    cells=con.execute('SELECT sum(policies),sum(exposure),sum(reported_claims) FROM region_age_cells').fetchone()
    check('Region-age cell reconciliation',all(math.isclose(x,y,rel_tol=1e-9) for x,y in zip(cells,m)),'Region-age cells conserve policy count, exposure and reported claims')
    return checks


def validate_segment_robustness(robustness, reporting):
    """Bootstrap summaries must refer to exactly the same SQL reporting population."""
    import numpy as np
    merged = robustness.merge(reporting, on=['dimension', 'segment'],
                              how='outer', suffixes=('_bootstrap', '_sql'),
                              indicator=True, validate='one_to_one')
    pairs = [('policies_bootstrap', 'policies_sql'),
             ('exposure_bootstrap', 'exposure_sql'),
             ('reported_claims_bootstrap', 'reported_claims_sql'),
             ('frequency_bootstrap', 'frequency_sql'),
             ('cost_per_year', 'recorded_cost_per_year')]
    if not merged['_merge'].eq('both').all() or not all(
            np.allclose(merged[a], merged[b], rtol=1e-9, atol=1e-9) for a, b in pairs):
        raise ValueError('Segment uncertainty reconciliation failed')
    return [{'check': 'Segment uncertainty reconciliation', 'status': 'PASS',
             'detail': 'Every bootstrap segment matches SQL policy count, exposure, claim count, frequency and cost rate'}]
