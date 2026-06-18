"""YAML oracle regression tests — verify diagnostics match baseline for all 33 YAML fixtures."""
from __future__ import annotations

import json
import os
import glob

import pytest

from tests.conftest import compile_text

_FIXTURES_DIR = '/home/dev/coze-studio/temp'
_BASELINE_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'expected', 'yaml_oracle_baseline.json')

with open(_BASELINE_FILE) as _f:
    _BASELINES = {b['fixture_id']: b for b in json.load(_f)}

_YAML_FILES = sorted(glob.glob(os.path.join(_FIXTURES_DIR, '*.yaml')))


@pytest.mark.parametrize("yaml_path", _YAML_FILES, ids=lambda p: os.path.basename(p))
def test_yaml_fixture_diagnostics(yaml_path):
    """Verify diagnostic rule_ids match baseline for each YAML fixture."""
    fixture_id = os.path.basename(yaml_path)
    baseline = _BASELINES.get(fixture_id)
    assert baseline is not None, f"No baseline for {fixture_id}"

    with open(yaml_path, 'r', encoding='utf-8') as f:
        text = f.read()

    report = compile_text(text)
    actual = sorted(d.rule_id for d in report.diagnostics)
    expected = baseline['rule_ids']

    assert actual == expected, (
        f"{fixture_id}: diagnostics mismatch\n"
        f"  expected ({len(expected)}): {expected}\n"
        f"  actual   ({len(actual)}): {actual}"
    )
