"""SYNTAX-004: versions should be object-like metadata."""
from __future__ import annotations

from tests.conftest import compile_text


def _ids(t):
    return sorted(d.rule_id for d in compile_text(t).diagnostics if d.rule_id.startswith('SYNTAX'))

VALID = (
    'nodes:\n'
    '  - id: "100001"\n'
    '    type: "1"\n'
    '    data:\n'
    '      nodeMeta:\n'
    '        title: "Start"\n'
    '  - id: "900001"\n'
    '    type: "2"\n'
    '    data:\n'
    '      nodeMeta:\n'
    '        title: "End"\n'
    'edges:\n'
    '  - sourceNodeID: "100001"\n'
    '    targetNodeID: "900001"\n'
)

class TestSYNTAX004_Positive:
    def test_no_versions(self):
        assert 'SYNTAX-004' not in _ids(VALID)
    def test_valid_versions_dict(self):
        t = VALID.replace('edges:\n', 'versions:\n  version: "1.0"\nedges:\n')
        assert 'SYNTAX-004' not in _ids(t)

class TestSYNTAX004_Negative:
    def test_versions_not_dict(self):
        t = VALID.replace('edges:\n', 'versions: "bad"\nedges:\n')
        assert 'SYNTAX-004' in _ids(t)
