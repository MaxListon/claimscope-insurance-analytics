"""Pinned-source build. Run from a checkout containing data/sources.json."""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import shutil
import ssl
import tempfile
import urllib.request
import certifi
import duckdb
import numpy as np
import rdata
from .quality import validate_inputs, validate_warehouse, validate_segment_robustness
from .statistics import frequency_interval, bootstrap_cost
from .model import fit_benchmark
from .presentation import render, memo
from .portfolio import standardize_regions, tail_diagnostics
from .robustness import segment_robustness


def digest(path):
    h=hashlib.sha256()
    with open(path,'rb') as file:
        for block in iter(lambda:file.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

@contextmanager
def build_lock(root):
    lock=root/'.build.lock'
    fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    try:
        os.write(fd,str(os.getpid()).encode());os.close(fd)
        yield
    finally: lock.unlink(missing_ok=True)

def sources(root,offline=False):
    metadata=json.loads((root/'data/sources.json').read_text())
    for name,info in metadata['files'].items():
        path=root/'data/raw'/name
        if not path.exists():
            if offline: raise FileNotFoundError(f'Missing pinned source: {path}')
            path.parent.mkdir(parents=True,exist_ok=True)
            tmp=path.with_suffix('.download')
            try:
                request=urllib.request.Request(info['url'],headers={'User-Agent':'ClaimScope/1.2'})
                with urllib.request.urlopen(request,timeout=120,context=ssl.create_default_context(cafile=certifi.where())) as response,open(tmp,'wb') as output:
                    shutil.copyfileobj(response,output)
                if digest(tmp)!=info['sha256']: raise ValueError(f'Source fingerprint mismatch: {name}')
                tmp.replace(path)
            finally: tmp.unlink(missing_ok=True)
        if digest(path)!=info['sha256']:raise ValueError(f'Source fingerprint mismatch: {name}')
    return metadata

def build(root,offline=False):
    root=Path(root).resolve()
    with build_lock(root):
        metadata=sources(root,offline)
        policies=rdata.read_rda(root/'data/raw/freMTPL2freq.rda')['freMTPL2freq']
        claims=rdata.read_rda(root/'data/raw/freMTPL2sev.rda')['freMTPL2sev']
        checks=validate_inputs(policies,claims)
        policies.IDpol=policies.IDpol.astype(str);claims.IDpol=claims.IDpol.astype(str)
        with tempfile.TemporaryDirectory(prefix='claimscope-',dir=root) as stage:
            stage=Path(stage)
            con=duckdb.connect(str(stage/'warehouse.duckdb'))
            try:
                con.register('p_input',policies);con.register('c_input',claims)
                con.execute('CREATE TABLE policies AS SELECT * FROM p_input')
                con.execute('CREATE TABLE claims AS SELECT * FROM c_input')
                for file in sorted((root/'sql').glob('*.sql')):con.execute(file.read_text())
                checks+=validate_warehouse(con)
                f=con.execute('SELECT * FROM policy_mart ORDER BY IDpol').df()
                segments=con.execute('SELECT * FROM segment_report ORDER BY dimension,segment').df()
                reconciliation=con.execute('SELECT * FROM reconciliation_report ORDER BY reconciliation_status').df()
                orphan=con.execute('SELECT count(*),coalesce(sum(ClaimAmount),0) FROM orphan_claims').fetchone()
                region_cells=con.execute('SELECT Region,driver_band,exposure,reported_claims AS claims FROM region_age_cells').df()
                naive=con.execute('SELECT sum(p.Exposure) FROM policies p LEFT JOIN claims c USING(IDpol)').fetchone()[0]
            finally:con.close()
            for i,row in segments.iterrows():
                lower,upper=frequency_interval(row.reported_claims,row.exposure)
                segments.loc[i,'frequency_lower']=lower;segments.loc[i,'frequency_upper']=upper
                segments.loc[i,'small_segment']=row.exposure<1000 or row.reported_claims<30
            total_amount=float(claims.ClaimAmount.sum())
            linked_amount=float(f.recorded_amount.sum())
            exposure=float(f.Exposure.sum())
            amount=claims.ClaimAmount.to_numpy(dtype=float)
            linked_claims=int(f.recorded_claims.sum())
            cutoff=float(np.quantile(amount,.99))
            # Cap each record independently, before grouping back to policies.
            cap=claims.assign(capped=np.minimum(amount,cutoff)).groupby('IDpol',observed=True).capped.sum()
            trimmed=claims.loc[claims.ClaimAmount<=cutoff].groupby('IDpol',observed=True).ClaimAmount.sum()
            sensitivity=[{'basis':'All linked amount records','cost_per_year':linked_amount/exposure},
              {'basis':'Each amount capped at source 99th percentile','cost_per_year':float(f.IDpol.map(cap).fillna(0).sum()/exposure)},
              {'basis':'Exclude records above source 99th percentile','cost_per_year':float(f.IDpol.map(trimmed).fillna(0).sum()/exposure)}]
            aligned=f[f.reconciliation_status=='Aligned']
            sensitivity.append({'basis':'Count-aligned policies only (selected subset)','cost_per_year':float(aligned.recorded_amount.sum()/aligned.Exposure.sum())})
            f['capped_recorded_amount']=f.IDpol.map(cap).fillna(0)
            robustness=segment_robustness(f)
            checks+=validate_segment_robustness(robustness,segments)
            model,calibration=fit_benchmark(f)
            regions,standardization=standardize_regions(f,cells=region_cells)
            support_sensitivity=[]
            region_scenarios={}
            for threshold in [50,100,250]:
                scenario,support=standardize_regions(f,minimum_cell_exposure=threshold,cells=region_cells)
                region_scenarios[str(threshold)]=json.loads(scenario.to_json(orient='records'))
                support_sensitivity.append(support)
            result={'segment_robustness':json.loads(robustness.to_json(orient='records')),'robustness_protocol':{'repetitions':400,'minimum_ranking_exposure':1000,'minimum_ranking_claims':30,'cost_cap':cutoff,'sampling':'Within-segment policy resampling; fixed segment sizes'},'region_scenarios':region_scenarios,'standardization':standardization,'support_sensitivity':support_sensitivity,'regions':json.loads(regions.to_json(orient='records')),'tail_influence':tail_diagnostics(claims,f),'source':metadata,'totals':{'policies':len(f),'exposure':exposure,'reported_claims':int(f.ClaimNb.sum()),'recorded_claims':linked_claims,'source_claim_records':len(claims),'source_amount':total_amount,'linked_amount':linked_amount,'orphan_records':int(orphan[0]),'orphan_amount':float(orphan[1]),'frequency':float(f.ClaimNb.sum()/exposure),'mean_recorded_claim':linked_amount/linked_claims,'cost_per_year':linked_amount/exposure,'mismatch_policies':int((f.reconciliation_status!='Aligned').sum()),'exposure_over_one':int((f.Exposure>1).sum()),'naive_join_exposure_inflation_pct':100*(naive/exposure-1),'largest_claim':float(amount.max()),'top_one_pct_amount_share':float(amount[amount>cutoff].sum()/total_amount),'p99_amount':cutoff,'cost_bootstrap_interval':bootstrap_cost(f),'frequency_interval':frequency_interval(int(f.ClaimNb.sum()),exposure)},'quality':checks,'segments':json.loads(segments.to_json(orient='records')),'reconciliation':json.loads(reconciliation.to_json(orient='records')),'sensitivity':sensitivity,'model':model,'calibration':json.loads(calibration.to_json(orient='records'))}
            reports=stage/'reports';reports.mkdir()
            (reports/'analysis.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
            segments.to_csv(reports/'segments.csv',index=False)
            regions.to_csv(reports/'regions.csv',index=False)
            robustness.to_csv(reports/'segment_robustness.csv',index=False)
            reconciliation.to_csv(reports/'reconciliation.csv',index=False)
            calibration.to_csv(reports/'calibration.csv',index=False)
            (reports/'EXECUTIVE_MEMO.md').write_text(memo(result))
            (reports/'quality.json').write_text(json.dumps(checks,indent=2)+'\n')
            # Generated HTML is offline-capable and contains aggregate results only.
            (stage/'index.html').write_text(render(result))
            inputs={str(p.relative_to(root)):digest(p) for p in sorted(p for p in (root/'src').rglob('*') if p.suffix in {'.py','.html','.css','.js'})+sorted((root/'sql').glob('*.sql'))+[root/'data/sources.json',root/'pyproject.toml',root/'requirements-lock.txt']}
            manifest={'schema_version':1,'inputs':inputs,'outputs':{str(p.relative_to(stage)):digest(p) for p in sorted(stage.rglob('*')) if p.is_file()}}
            (reports/'build_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
            # Stage all computations before publication. Per-file replacements are atomic;
            # this is a single-user batch tool, not a concurrent report-serving backend.
            (root/'reports').mkdir(exist_ok=True);(root/'docs').mkdir(exist_ok=True)
            (root/'docs/reports').mkdir(exist_ok=True)
            for p in reports.iterdir():
                shutil.copyfile(p,root/'docs/reports'/p.name)
                os.replace(p,root/'reports'/p.name)
            os.replace(stage/'index.html',root/'docs/index.html')
            os.replace(stage/'warehouse.duckdb',root/'data/warehouse.duckdb')
    print(json.dumps({'policies':len(f),'quality_checks':len(checks),'test_deviance_improvement_pct':model['deviance_improvement_pct'],'dashboard':str(root/'docs/index.html')},indent=2))
    return result

def main():
    p=argparse.ArgumentParser(description='Build the ClaimScope portfolio and audit evidence')
    p.add_argument('--root',type=Path,default=Path.cwd());p.add_argument('--offline',action='store_true')
    a=p.parse_args();build(a.root,a.offline)

if __name__=='__main__':main()
