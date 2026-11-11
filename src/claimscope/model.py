"""Exposure-weighted frequency benchmark with frozen diagnostic extensions."""
import hashlib
import warnings

import numpy as np
import pandas as pd
from scipy.special import xlogy
from sklearn.compose import ColumnTransformer
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import PoissonRegressor
from sklearn.metrics import mean_poisson_deviance
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder

FEATURES = ['driver_band', 'vehicle_band', 'bonus_band', 'Area', 'VehGas', 'Region', 'VehPower']


def partition(identifier):
    value = int(hashlib.sha256(('claimscope-v1:' + str(identifier)).encode()).hexdigest()[:8], 16) % 100
    return 'train' if value < 60 else ('validation' if value < 80 else 'test')


def paired_deviance_interval(y, prediction, baseline, exposure, repetitions=400, seed=20261111):
    """Pair policy resamples; retain each policy's outcome, exposure and both scores."""
    y = np.asarray(y, dtype=float)
    exposure = np.asarray(exposure, dtype=float)
    prediction = np.asarray(prediction, dtype=float)
    model_loss = 2 * exposure * (xlogy(y, y / prediction) - y + prediction)
    baseline_loss = 2 * exposure * (xlogy(y, y / baseline) - y + baseline)
    rng = np.random.default_rng(seed)
    improvements = []
    for _ in range(repetitions):
        sample = rng.integers(0, len(y), len(y))
        denominator = baseline_loss[sample].sum()
        if denominator > 0:
            improvements.append(100 * (1 - model_loss[sample].sum() / denominator))
    if not improvements:
        raise ValueError('Deviance improvement is undefined for this sample')
    return [float(v) for v in np.quantile(improvements, [.025, .975])]


def fit_benchmark(frame):
    f = frame.copy()
    f['split'] = f.IDpol.map(partition)
    x = f[FEATURES].astype(str)
    y = f.ClaimNb / f.Exposure
    train, valid, test = [f.split == label for label in ['train', 'validation', 'test']]
    baseline = f.loc[train, 'ClaimNb'].sum() / f.loc[train, 'Exposure'].sum()

    def fit(features, alpha):
        model = make_pipeline(
            ColumnTransformer([('category', OneHotEncoder(handle_unknown='ignore'), features)]),
            PoissonRegressor(alpha=alpha, max_iter=500, tol=1e-7),
        )
        # A model that silently hits its optimizer limit must not become a release.
        with warnings.catch_warnings():
            warnings.simplefilter('error', ConvergenceWarning)
            model.fit(x[train], y[train], poissonregressor__sample_weight=f.loc[train, 'Exposure'])
        return model

    candidates, models = [], []
    for alpha in [.001, .01, .1]:
        model = fit(FEATURES, alpha)
        score = mean_poisson_deviance(y[valid], model.predict(x[valid]), sample_weight=f.loc[valid, 'Exposure'])
        candidates.append({'alpha': alpha, 'validation_deviance': float(score)})
        models.append(model)
    choice = int(np.argmin([v['validation_deviance'] for v in candidates]))
    alpha = candidates[choice]['alpha']
    prediction = models[choice].predict(x[test])
    held = f.loc[test].copy()
    held['predicted_rate'] = prediction
    held['expected_claims'] = prediction * held.Exposure
    held['risk_decile'] = pd.qcut(held.predicted_rate.rank(method='first'), 10, labels=False) + 1
    cal = held.groupby('risk_decile', observed=True).agg(
        policies=('IDpol', 'size'), exposure=('Exposure', 'sum'),
        observed=('ClaimNb', 'sum'), expected=('expected_claims', 'sum'),
    ).reset_index()
    cal['observed_rate'] = cal.observed / cal.exposure
    cal['predicted_rate'] = cal.expected / cal.exposure

    def score(pred):
        return float(mean_poisson_deviance(y[test], pred, sample_weight=held.Exposure))

    benchmark = score(np.repeat(baseline, len(held)))
    fitted = score(prediction)
    # Diagnostic requested after the original holdout was examined: keep alpha and
    # partition frozen. This is a sensitivity analysis, not a new untouched test.
    no_bonus = fit([v for v in FEATURES if v != 'bonus_band'], alpha)
    no_bonus_prediction = no_bonus.predict(x[test])
    no_bonus_score = score(no_bonus_prediction)
    return {
        'split_counts': f.split.value_counts().to_dict(), 'candidates': candidates,
        'selected_alpha': alpha, 'test_deviance': fitted,
        'baseline_test_deviance': benchmark,
        'deviance_improvement_pct': 100 * (1 - fitted / benchmark),
        'test_observed_claims': float(held.ClaimNb.sum()),
        'test_expected_claims': float(held.expected_claims.sum()),
        'test_exposure': float(held.Exposure.sum()), 'train_baseline_rate': float(baseline),
        'improvement_interval_pct': paired_deviance_interval(y[test], prediction, baseline, held.Exposure),
        'bootstrap_repetitions': 400,
        'no_bonus_test_deviance': no_bonus_score,
        'no_bonus_improvement_pct': 100 * (1 - no_bonus_score / benchmark),
        'no_bonus_test_expected_claims': float((no_bonus_prediction * held.Exposure).sum()),
        'diagnostic_scope': 'Post-holdout sensitivity; fixed original split and selected alpha',
    }, cal
