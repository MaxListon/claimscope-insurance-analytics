"""Prespecified portfolio-mix and large-claim sensitivity diagnostics."""
import numpy as np
import pandas as pd


def standardize_regions(frame, minimum_cell_exposure=100, cells=None):
    """Direct age standardization to the full portfolio's exposure mix.

    Require every reference age band to meet the cell exposure threshold.
    Unsupported regions remain visible; never reweight around missing strata.
    """
    if minimum_cell_exposure < 0:
        raise ValueError('Minimum cell exposure cannot be negative')
    reference=frame.groupby('driver_band',observed=True).Exposure.sum().sort_index()
    weights=reference/reference.sum()
    if cells is None:
        cells=frame.groupby(['Region','driver_band'],observed=True).agg(
            exposure=('Exposure','sum'),claims=('ClaimNb','sum')).reset_index()
    rows=[]
    for region,group in cells.groupby('Region',observed=True,sort=True):
        g=group.set_index('driver_band').reindex(weights.index)
        complete=bool(g.exposure.notna().all() and (g.exposure>0).all())
        supported=complete and bool((g.exposure>=minimum_cell_exposure).all())
        exposure=float(group.exposure.sum());claims=int(group.claims.sum())
        standardized=float((weights*g.claims/g.exposure).sum()) if supported else None
        # Model-based variance assumes independent Poisson cell counts.
        se=float(np.sqrt((weights.pow(2)*g.claims/g.exposure.pow(2)).sum())) if supported else None
        rows.append({'region':str(region),'exposure':exposure,'claims':claims,
          'crude_rate':claims/exposure,'standardized_rate':standardized,
          'standardized_lower':max(0.,standardized-1.96*se) if supported else None,
          'standardized_upper':standardized+1.96*se if supported else None,
          'minimum_cell_exposure':float(g.exposure.min()) if complete else 0.,
          'supported':supported,'reason':'All reference age bands supported' if supported else 'Insufficient exposure in at least one reference age band'})
    result=pd.DataFrame(rows)
    supported=result.supported
    result.loc[supported,'crude_rank']=result.loc[supported,'crude_rate'].rank(method='min',ascending=False)
    result.loc[supported,'standardized_rank']=result.loc[supported,'standardized_rate'].rank(method='min',ascending=False)
    result['rank_change']=result.crude_rank-result.standardized_rank
    return result,{'minimum_cell_exposure':minimum_cell_exposure,
      'reference_weights':{str(k):float(v) for k,v in weights.items()},
      'supported_regions':int(supported.sum()),'total_regions':len(result),
      'supported_exposure_share':float(result.loc[supported,'exposure'].sum()/frame.Exposure.sum())}



def tail_diagnostics(claims, policies):
    """Cumulative influence, not disjoint slices; preserve all policy exposure."""
    amounts=claims.sort_values('ClaimAmount',ascending=False,kind='stable')
    total=float(amounts.ClaimAmount.sum())
    linked=amounts[amounts.IDpol.isin(policies.IDpol)]
    linked_total=float(linked.ClaimAmount.sum())
    exposure=float(policies.Exposure.sum())
    return [{'records':min(k,len(amounts)),
       'source_amount_share':float(amounts.head(k).ClaimAmount.sum()/total),
       'linked_cost_without_records_per_year':float((linked_total-amounts.head(k).loc[lambda x:x.IDpol.isin(policies.IDpol),'ClaimAmount'].sum())/exposure)} for k in [1,5,10]]
