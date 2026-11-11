"""Detect stale or changed report artifacts, including the published copies."""
import hashlib
import json
from pathlib import Path


def verify(root):
    manifest = json.loads((root / 'reports/build_manifest.json').read_text())
    for path, expected in manifest['inputs'].items():
        actual = hashlib.sha256((root / path).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f'Stale input: {path}')
    for path, expected in manifest['outputs'].items():
        target = (root / 'data/warehouse.duckdb' if path == 'warehouse.duckdb'
                  else root / 'docs/index.html' if path == 'index.html'
                  else root / path)
        if path == 'warehouse.duckdb' and not target.exists():
            continue
        if hashlib.sha256(target.read_bytes()).hexdigest() != expected:
            raise ValueError(f'Changed output: {path}')
    published = [path for path in manifest['outputs'] if path.startswith('reports/')]
    published.append('reports/build_manifest.json')
    for path in published:
        source = root / path
        if source.read_bytes() != (root / 'docs' / path).read_bytes():
            raise ValueError(f'Published report copy differs: {path}')
    return manifest


if __name__ == '__main__':
    verify(Path(__file__).resolve().parents[1])
    print('Inputs, report artifacts, and published report copies match the build manifest.')
