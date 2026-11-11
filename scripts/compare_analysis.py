"""Compare numerical reproduction with a documented floating-point tolerance."""
import json,math,sys

def compare(a,b,path='root'):
    if isinstance(a,dict):
        assert a.keys()==b.keys(),f'{path}: keys differ'
        for k in a:compare(a[k],b[k],f'{path}.{k}')
    elif isinstance(a,list):
        assert len(a)==len(b),f'{path}: length differs'
        for i,(x,y) in enumerate(zip(a,b)):compare(x,y,f'{path}[{i}]')
    elif isinstance(a,float):
        assert math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-9),f'{path}: {a} != {b}'
    else:assert a==b,f'{path}: {a} != {b}'

if __name__=='__main__':
    compare(json.load(open(sys.argv[1])),json.load(open(sys.argv[2])))
    print('Analysis matches (numeric tolerance: relative/absolute 1e-9).')
