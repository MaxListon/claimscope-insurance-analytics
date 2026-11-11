"""Detect stale/tampered committed report inputs and outputs."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
m=json.loads((root/'reports/build_manifest.json').read_text())
for path,expected in m['inputs'].items():
    assert hashlib.sha256((root/path).read_bytes()).hexdigest()==expected,f'Stale input: {path}'
for path,expected in m['outputs'].items():
    target=root/'data/warehouse.duckdb' if path=='warehouse.duckdb' else root/'docs/index.html' if path=='index.html' else root/path
    if path=='warehouse.duckdb' and not target.exists():continue
    assert hashlib.sha256(target.read_bytes()).hexdigest()==expected,f'Changed output: {path}'
print('All tracked inputs and report outputs match the build manifest.')
