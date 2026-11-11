from pathlib import Path
import duckdb
import pandas as pd
import pytest
from claimscope.quality import validate_inputs,validate_warehouse
from claimscope.statistics import frequency_interval,bootstrap_cost
from claimscope.model import partition
from claimscope.pipeline import build_lock,sources

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture
def portfolio():
    # Three policies, one with two distinct source claim records; one zero-claim.
    p=pd.DataFrame({'IDpol':['a','b','c'],'ClaimNb':[2.,0.,1.],'Exposure':[1.,.5,1.],
    'VehPower':[5,6,7],'VehAge':[2,4,20],'DrivAge':[23,40,70],'BonusMalus':[50,80,120],
    'VehBrand':['B1']*3,'VehGas':['Diesel']*3,'Area':['A']*3,'Density':[1,2,3],'Region':['R']*3})
    c=pd.DataFrame({'IDpol':['a','a','x'],'ClaimAmount':[10.,20.,40.]})
    return p,c

def warehouse(p,c):
    con=duckdb.connect();con.register('p',p);con.register('c',c)
    con.execute('CREATE TABLE policies AS SELECT * FROM p');con.execute('CREATE TABLE claims AS SELECT * FROM c')
    for file in sorted((ROOT/'sql').glob('*.sql')):con.execute(file.read_text())
    return con

def test_join_does_not_multiply_exposure(portfolio):
    con=warehouse(*portfolio)
    assert con.execute('SELECT sum(Exposure) FROM policy_mart').fetchone()[0]==2.5
    assert con.execute('SELECT count(*) FROM policy_mart').fetchone()[0]==3
    assert con.execute("SELECT recorded_amount FROM policy_mart WHERE IDpol='a'").fetchone()[0]==30
    checks=validate_warehouse(con)
    assert all(c['status']=='PASS' for c in checks)
    names=[c['check'] for c in checks if c['check'].startswith('Segment reconciliation:')]
    assert names==sorted(names)
    con.close()

def test_zero_claim_and_orphan_retained(portfolio):
    con=warehouse(*portfolio)
    assert con.execute("SELECT recorded_claims,recorded_amount FROM policy_mart WHERE IDpol='b'").fetchone()==(0,0)
    assert con.execute('SELECT sum(ClaimAmount) FROM orphan_claims').fetchone()[0]==40
    assert con.execute("SELECT reconciliation_status FROM policy_mart WHERE IDpol='c'").fetchone()[0]=='Fewer amount records'
    con.close()

def test_corrupt_mart_blocks_build(portfolio):
    con=warehouse(*portfolio);con.execute('UPDATE policy_mart SET Exposure=Exposure*2')
    with pytest.raises(ValueError,match='Exposure conservation'):validate_warehouse(con)
    con.close()

@pytest.mark.parametrize('field,value',[('Exposure',0),('Exposure',-1),('Exposure',float('inf')),('ClaimNb',.5),('ClaimNb',-1),('DrivAge',None)])
def test_invalid_policy_blocked(portfolio,field,value):
    p,c=portfolio;p.loc[0,field]=value
    with pytest.raises(ValueError):validate_inputs(p,c)

def test_duplicate_policy_blocked(portfolio):
    p,c=portfolio;p.loc[1,'IDpol']='a'
    with pytest.raises(ValueError,match='duplicate'):validate_inputs(p,c)

def test_identical_amount_records_not_removed(portfolio):
    p,c=portfolio;c.loc[1,'ClaimAmount']=10
    con=warehouse(p,c)
    assert con.execute("SELECT recorded_claims FROM policy_mart WHERE IDpol='a'").fetchone()[0]==2
    con.close()

def test_claim_amount_must_be_positive(portfolio):
    p,c=portfolio;c.loc[0,'ClaimAmount']=0
    with pytest.raises(ValueError):validate_inputs(p,c)

def test_poisson_zero_count_upper_bound():
    lo,hi=frequency_interval(0,100)
    assert lo==0;assert hi==pytest.approx(.0368887945)

def test_poisson_rate_scales_with_exposure():
    a=frequency_interval(10,100);b=frequency_interval(10,200)
    assert b==pytest.approx([x/2 for x in a])

@pytest.mark.parametrize('count,exposure',[(1,0),(-1,2),(.2,10)])
def test_invalid_interval(count,exposure):
    with pytest.raises(ValueError):frequency_interval(count,exposure)

def test_bootstrap_resamples_policy_pairs():
    frame=pd.DataFrame({'Exposure':[1.,2.,3.],'recorded_amount':[10.,20.,30.]})
    assert bootstrap_cost(frame,repetitions=50)==pytest.approx([10,10])

def test_split_deterministic_and_disjoint():
    ids=[str(i) for i in range(1000)]
    assignment={i:partition(i) for i in ids}
    assert assignment=={i:partition(i) for i in reversed(ids)}
    assert set(assignment.values())=={'train','validation','test'}

def test_second_writer_rejected(tmp_path):
    with build_lock(tmp_path):
        with pytest.raises(FileExistsError):
            with build_lock(tmp_path):pass
    assert not (tmp_path/'.build.lock').exists()

def test_lock_released_after_exception(tmp_path):
    with pytest.raises(RuntimeError):
        with build_lock(tmp_path):raise RuntimeError('intentional')
    assert not (tmp_path/'.build.lock').exists()

def test_tampered_source_rejected(tmp_path):
    import json
    (tmp_path/'data/raw').mkdir(parents=True)
    (tmp_path/'data/sources.json').write_text(json.dumps({'files':{'x.rda':{'sha256':'0'*64}}}))
    (tmp_path/'data/raw/x.rda').write_bytes(b'corrupt')
    with pytest.raises(ValueError,match='fingerprint'):sources(tmp_path,offline=True)

def test_test_outcomes_cannot_change_predictions_or_selection(portfolio):
    from claimscope.model import fit_benchmark
    import numpy as np
    p,_=portfolio
    f=pd.concat([p.iloc[[i%3]].assign(IDpol=str(i)) for i in range(400)],ignore_index=True)
    f['driver_band']=np.where(f.DrivAge<25,'18–24','25+')
    f['vehicle_band']='all';f['bonus_band']='all'
    original,calibration=fit_benchmark(f)
    changed=f.copy();changed.loc[changed.IDpol.map(partition)=='test','ClaimNb']+=3
    revised,new_calibration=fit_benchmark(changed)
    assert original['candidates']==revised['candidates']
    assert original['selected_alpha']==revised['selected_alpha']
    assert original['test_expected_claims']==pytest.approx(revised['test_expected_claims'])
    assert list(calibration.expected)==pytest.approx(list(new_calibration.expected))
    assert original['test_observed_claims']!=revised['test_observed_claims']
