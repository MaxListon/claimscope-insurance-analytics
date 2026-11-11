"""Exploratory exposure-weighted frequency benchmark; no pricing endpoint."""
import hashlib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import PoissonRegressor
from sklearn.pipeline import make_pipeline
from sklearn.metrics import mean_poisson_deviance

FEATURES=['driver_band','vehicle_band','bonus_band','Area','VehGas','Region','VehPower']

def partition(identifier):
    value=int(hashlib.sha256(('claimscope-v1:'+str(identifier)).encode()).hexdigest()[:8],16)%100
    return 'train' if value<60 else ('validation' if value<80 else 'test')

def fit_benchmark(frame):
    f=frame.copy()
    f['split']=f.IDpol.map(partition)
    x=f[FEATURES].astype(str)
    y=f.ClaimNb/f.Exposure
    train=f.split=='train'; valid=f.split=='validation'; test=f.split=='test'
    baseline=f.loc[train,'ClaimNb'].sum()/f.loc[train,'Exposure'].sum()
    candidates=[]; models=[]
    for alpha in [.001,.01,.1]:
        model=make_pipeline(ColumnTransformer([('category',OneHotEncoder(handle_unknown='ignore'),FEATURES)]),PoissonRegressor(alpha=alpha,max_iter=500,tol=1e-7))
        model.fit(x[train],y[train],poissonregressor__sample_weight=f.loc[train,'Exposure'])
        score=mean_poisson_deviance(y[valid],model.predict(x[valid]),sample_weight=f.loc[valid,'Exposure'])
        candidates.append({'alpha':alpha,'validation_deviance':float(score)})
        models.append(model)
    choice=int(np.argmin([v['validation_deviance'] for v in candidates]))
    prediction=models[choice].predict(x[test])
    held=f.loc[test].copy();held['predicted_rate']=prediction
    held['expected_claims']=prediction*held.Exposure
    held['risk_decile']=pd.qcut(held.predicted_rate.rank(method='first'),10,labels=False)+1
    cal=held.groupby('risk_decile',observed=True).agg(policies=('IDpol','size'),exposure=('Exposure','sum'),observed=('ClaimNb','sum'),expected=('expected_claims','sum')).reset_index()
    cal['observed_rate']=cal.observed/cal.exposure;cal['predicted_rate']=cal.expected/cal.exposure
    score=lambda pred:float(mean_poisson_deviance(y[test],pred,sample_weight=held.Exposure))
    benchmark=score(np.repeat(baseline,len(held)))
    fitted=score(prediction)
    return {'split_counts':f.split.value_counts().to_dict(),'candidates':candidates,'selected_alpha':candidates[choice]['alpha'],'test_deviance':fitted,'baseline_test_deviance':benchmark,'deviance_improvement_pct':100*(1-fitted/benchmark),'test_observed_claims':float(held.ClaimNb.sum()),'test_expected_claims':float(held.expected_claims.sum()),'test_exposure':float(held.Exposure.sum()),'train_baseline_rate':float(baseline)},cal
