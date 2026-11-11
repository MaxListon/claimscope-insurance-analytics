"""Counterexamples that distinguish adjustment from a cosmetic re-ranking."""
import numpy as np
import pandas as pd
import pytest

from claimscope.portfolio import standardize_regions, tail_diagnostics
from claimscope.model import paired_deviance_interval


def mix_fixture():
    return pd.DataFrame({'IDpol':['a','b','c','d'], 'Region':['A','A','B','B'],
       'driver_band':['young','old','young','old'],
       'Exposure':[900.,100.,100.,900.], 'ClaimNb':[180.,10.,40.,135.]})


def test_common_mix_can_reverse_crude_ranking():
    report,meta=standardize_regions(mix_fixture())
    a,b=[report.set_index('region').loc[r] for r in ['A','B']]
    assert a.crude_rate>b.crude_rate
    assert a.standardized_rate<b.standardized_rate
    assert a.standardized_rate==pytest.approx(.15)
    assert b.standardized_rate==pytest.approx(.275)
    assert meta['reference_weights']==pytest.approx({'young':.5,'old':.5})
    assert meta['supported_exposure_share']==1


def test_support_threshold_does_not_silently_change_weights():
    frame=mix_fixture()
    report,meta=standardize_regions(frame,minimum_cell_exposure=101)
    assert not report.supported.any()
    assert report.standardized_rate.isna().all()
    assert meta['supported_exposure_share']==0
    assert meta['reference_weights']==pytest.approx({'young':.5,'old':.5})


def test_missing_stratum_remains_unsupported():
    frame=mix_fixture().drop(index=2)
    report,_=standardize_regions(frame,minimum_cell_exposure=0)
    b=report.set_index('region').loc['B']
    assert not b.supported
    assert pd.isna(b.standardized_rate)
    assert pd.isna(b.standardized_rank)


def test_ranks_use_supported_regions_only():
    frame=mix_fixture()
    frame=pd.concat([frame,pd.DataFrame({'IDpol':['e'],'Region':['C'],'driver_band':['old'],'Exposure':[1.],'ClaimNb':[5.]})])
    report,_=standardize_regions(frame)
    assert set(report.loc[report.supported,'crude_rank'])=={1.,2.}
    assert pd.isna(report.set_index('region').loc['C','crude_rank'])


def test_negative_support_threshold_rejected():
    with pytest.raises(ValueError):standardize_regions(mix_fixture(),-1)


def test_tail_excludes_orphan_amounts_from_linked_cost():
    policies=pd.DataFrame({'IDpol':['a','b'],'Exposure':[1.,1.]})
    claims=pd.DataFrame({'IDpol':['orphan','a','b'],'ClaimAmount':[100.,20.,10.]})
    top=tail_diagnostics(claims,policies)[0]
    assert top['source_amount_share']==pytest.approx(100/130)
    assert top['linked_cost_without_records_per_year']==15


def test_paired_interval_for_identical_models_is_zero():
    assert paired_deviance_interval(np.array([0.,1.,2.]),np.array([1.,1.,1.]),1.,np.ones(3),repetitions=40)==pytest.approx([0.,0.])
