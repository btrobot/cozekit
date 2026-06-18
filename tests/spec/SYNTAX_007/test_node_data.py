"""SYNTAX-007: node must have data."""
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

class TestSYNTAX007_Positive:
    def test_has_data(self):
        assert 'SYNTAX-007' not in _ids(VALID)

class TestSYNTAX007_Negative:
    def test_missing_data(self):
        t = 'nodes:\n  - id: "n1"\n    type: "1"\nedges: []\n'
        assert 'SYNTAX-007' in _ids(t)
