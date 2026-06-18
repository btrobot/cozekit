"""SYNTAX-006: node must have a type."""
from __future__ import annotations
from tests.conftest import compile_text

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


def _ids(t):
    return sorted(d.rule_id for d in compile_text(t).diagnostics if d.rule_id.startswith('SYNTAX'))


class TestSYNTAX006_Positive:
    def test_has_type(self):
        assert 'SYNTAX-006' not in _ids(VALID)


class TestSYNTAX006_Negative:
    def test_missing_type(self):
        t = 'nodes:\n  - id: "n1"\n    data: {}\nedges: []'
        assert 'SYNTAX-006' in _ids(t)
