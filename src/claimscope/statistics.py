"""Intervals and sensitivity calculations; no simulated observations."""
import numpy as np
from scipy.stats import chi2

def frequency_interval(claims, exposure, confidence=.95):
    """Exact Poisson rate interval under an independent Poisson count assumption."""
    if exposure<=0 or claims<0 or int(claims)!=claims or not 0<confidence<1:
        raise ValueError("Nonnegative integer count, positive exposure, valid confidence required")
    a=1-confidence
    return (0. if claims==0 else float(chi2.ppf(a/2,2*claims)/2/exposure),
            float(chi2.ppf(1-a/2,2*(claims+1))/2/exposure))

def bootstrap_cost(frame, repetitions=400, seed=20261110):
    """Resample policies, retaining all claims on each sampled policy."""
    rng=np.random.default_rng(seed)
    # Multinomial counts over unique policy outcomes compress zero-claim policies
    # without changing the empirical policy bootstrap distribution.
    values=frame[['Exposure','recorded_amount']].to_numpy(dtype=float)
    unique,counts=np.unique(values,axis=0,return_counts=True)
    draws=rng.multinomial(len(values),counts/len(values),size=repetitions)
    rates=(draws@unique[:,1])/(draws@unique[:,0])
    return [float(x) for x in np.quantile(rates,[.025,.975])]
