"""SYNTAX-014/015: canonical start/end node IDs."""
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

class TestSYNTAX014_015_Positive:
    def test_canonical_ids(self):
        ids = _ids(VALID)
        assert 'SYNTAX-014' not in ids
        assert 'SYNTAX-015' not in ids

class TestSYNTAX014_015_Negative:
    def test_wrong_start_id(self):
        t = VALID.replace('100001', '000001')
        assert 'SYNTAX-014' in _ids(t)
    def test_wrong_end_id(self):
        t = VALID.replace('900001', '000002')
        assert 'SYNTAX-015' in _ids(t)
