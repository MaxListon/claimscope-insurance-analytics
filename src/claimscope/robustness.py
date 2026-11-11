"""Policy-level sampling uncertainty and tail sensitivity for reporting segments."""
import hashlib

import numpy as np
import pandas as pd

DIMENSIONS = {
    'Region': 'Region', 'Driver age': 'driver_band',
    'Vehicle age': 'vehicle_band', 'Bonus / malus': 'bonus_band',
    'Area': 'Area', 'Fuel': 'VehGas',
}


def bootstrap_rates(frame, repetitions=400, seed=20261112):
    """Resample full policies using compressed empirical outcome multiplicities.

    Frequency and cost use the SAME draw and exposure denominator. Batches bound
    temporary memory independently of the requested repetition count.
    """
    values = frame[['Exposure', 'ClaimNb', 'recorded_amount']].to_numpy(dtype=float)
    if len(values) == 0 or not np.isfinite(values).all() or (values[:, 0] <= 0).any():
        raise ValueError('Nonempty finite policy data with positive exposure required')
    if (values[:, 1:] < 0).any() or (values[:, 1] % 1 != 0).any():
        raise ValueError('Nonnegative integer counts and nonnegative amounts required')
    if repetitions < 2:
        raise ValueError('At least two bootstrap repetitions required')
    unique, counts = np.unique(values, axis=0, return_counts=True)
    rng = np.random.default_rng(seed)
    rates = []
    for start in range(0, repetitions, 25):
        draw = rng.multinomial(len(values), counts / len(values), size=min(25, repetitions-start))
        exposure = draw @ unique[:, 0]
        rates.append(np.column_stack((draw @ unique[:, 1] / exposure,
                                      draw @ unique[:, 2] / exposure)))
    return np.vstack(rates)


def segment_robustness(frame, repetitions=400):
    """Fixed segment sizes; intervals and exploratory rank stability, not forecasts."""
    records = []
    for dimension, column in DIMENSIONS.items():
        groups = []
        for segment, group in frame.groupby(column, observed=True, sort=True):
            namespace = f'claimscope-segment-v1:{dimension}:{segment}'
            seed = int(hashlib.sha256(namespace.encode()).hexdigest()[:8], 16)
            draws = bootstrap_rates(group, repetitions, seed)
            intervals = np.quantile(draws, [.025, .975], axis=0)
            exposure = float(group.Exposure.sum())
            amount = float(group.recorded_amount.sum())
            count = int(group.ClaimNb.sum())
            eligible = exposure >= 1000 and count >= 30
            records.append({
                'dimension': dimension, 'segment': str(segment), 'policies': len(group),
                'exposure': exposure, 'reported_claims': count,
                'frequency': count / exposure,
                'frequency_bootstrap_lower': float(intervals[0, 0]),
                'frequency_bootstrap_upper': float(intervals[1, 0]),
                'cost_per_year': amount / exposure,
                'cost_bootstrap_lower': float(intervals[0, 1]),
                'cost_bootstrap_upper': float(intervals[1, 1]),
                'capped_cost_per_year': float(group.capped_recorded_amount.sum() / exposure),
                'largest_policy_amount_share': float(group.recorded_amount.max() / amount) if amount else 0.,
                'ranking_eligible': eligible,
                'cost_rank': None, 'capped_cost_rank': None,
                'cost_top_quartile_resample_share': None,
            })
            groups.append((len(records)-1, draws[:, 1], eligible))
        eligible_groups = [(i, draws) for i, draws, eligible in groups if eligible]
        if not eligible_groups:
            continue
        indices = [i for i, _ in eligible_groups]
        matrix = np.column_stack([draws for _, draws in eligible_groups])
        top_count = max(1, int(np.ceil(len(indices) / 4)))
        # Stable label order breaks ties; this is a descriptive resample share,
        # not a posterior probability that a segment is intrinsically risky.
        top = np.argsort(-matrix, axis=1, kind='stable')[:, :top_count]
        original = pd.Series([records[i]['cost_per_year'] for i in indices]).rank(method='min', ascending=False)
        capped = pd.Series([records[i]['capped_cost_per_year'] for i in indices]).rank(method='min', ascending=False)
        for column_index, index in enumerate(indices):
            records[index]['cost_rank'] = int(original.iloc[column_index])
            records[index]['capped_cost_rank'] = int(capped.iloc[column_index])
            records[index]['cost_top_quartile_resample_share'] = float((top == column_index).any(axis=1).mean())
    return pd.DataFrame(records).sort_values(['dimension', 'segment']).reset_index(drop=True)
