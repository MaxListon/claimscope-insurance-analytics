"""Verify bootstrap units, denominators, eligibility and rank definitions."""
import numpy as np
import pandas as pd
import pytest
from claimscope.robustness import bootstrap_rates, segment_robustness


def fixture_frame():
    return pd.DataFrame({'Exposure':[1000.,1000.,1000.,1.],
      'ClaimNb':[50.,40.,35.,0.], 'recorded_amount':[100.,80.,60.,0.],
      'capped_recorded_amount':[20.,80.,60.,0.],
      **{k:['A','B','C','D'] for k in ['Region','driver_band','vehicle_band','bonus_band','Area','VehGas']}})


def test_paired_policy_denominator_is_preserved():
    frame=pd.DataFrame({'Exposure':[1.,2.,3.],'ClaimNb':[2.,4.,6.],'recorded_amount':[10.,20.,30.]})
    draws=bootstrap_rates(frame,repetitions=50)
    assert draws[:,0]==pytest.approx(np.repeat(2.,50))
    assert draws[:,1]==pytest.approx(np.repeat(10.,50))


def test_zero_claim_policies_are_part_of_the_sample():
    frame=pd.DataFrame({'Exposure':[1.,1.],'ClaimNb':[0.,1.],'recorded_amount':[0.,10.]})
    draws=bootstrap_rates(frame,repetitions=400)
    assert draws[:,0].min()==0
    assert draws[:,0].max()==1
    assert draws[:,1]==pytest.approx(draws[:,0]*10)


def test_bootstrap_deterministic_and_independent_of_row_order():
    frame=fixture_frame()
    assert np.array_equal(bootstrap_rates(frame,50,77),bootstrap_rates(frame.iloc[::-1],50,77))


@pytest.mark.parametrize('column,value',[('Exposure',0),('Exposure',float('inf')),('ClaimNb',.5),('recorded_amount',-1)])
def test_invalid_policy_data_rejected(column,value):
    frame=fixture_frame();frame.loc[0,column]=value
    with pytest.raises(ValueError):bootstrap_rates(frame,20)


def test_capped_rank_changes_without_changing_exposure():
    result=segment_robustness(fixture_frame(),40)
    region=result[result.dimension=='Region'].set_index('segment')
    assert region.loc['A','cost_rank']==1
    assert region.loc['A','capped_cost_rank']==3
    assert region.loc['A','cost_top_quartile_resample_share']==1
    assert region.loc['B','cost_top_quartile_resample_share']==0
    assert region.loc['A','exposure']==1000
    assert not region.loc['D','ranking_eligible']
    assert pd.isna(region.loc['D','cost_rank'])


def test_bootstrap_repetitions_are_validated():
    with pytest.raises(ValueError):bootstrap_rates(fixture_frame(),1)
