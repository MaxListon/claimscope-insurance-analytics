"""Artifact contracts must reject stale inputs and divergent published copies."""
import hashlib
import importlib.util
import json
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('artifact_verifier',ROOT/'scripts/verify_artifacts.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


@pytest.fixture
def snapshot(tmp_path):
    (tmp_path/'reports').mkdir();(tmp_path/'docs/reports').mkdir(parents=True)
    (tmp_path/'source.py').write_text('version = 1')
    (tmp_path/'reports/result.json').write_text('{"measured": 7}')
    digest=lambda p:hashlib.sha256((tmp_path/p).read_bytes()).hexdigest()
    manifest={'inputs':{'source.py':digest('source.py')},'outputs':{'reports/result.json':digest('reports/result.json')}}
    (tmp_path/'reports/build_manifest.json').write_text(json.dumps(manifest))
    for name in ['result.json','build_manifest.json']:
        (tmp_path/'docs/reports'/name).write_bytes((tmp_path/'reports'/name).read_bytes())
    return tmp_path


def test_valid_snapshot_is_accepted(snapshot):
    assert module.verify(snapshot)['inputs']


def test_stale_source_rejected(snapshot):
    (snapshot/'source.py').write_text('version = 2')
    with pytest.raises(ValueError,match='Stale input'):module.verify(snapshot)


def test_changed_report_rejected(snapshot):
    (snapshot/'reports/result.json').write_text('{"measured": 99}')
    with pytest.raises(ValueError,match='Changed output'):module.verify(snapshot)


def test_divergent_published_copy_rejected(snapshot):
    (snapshot/'docs/reports/result.json').write_text('{"measured": 99}')
    with pytest.raises(ValueError,match='Published report copy differs'):module.verify(snapshot)
