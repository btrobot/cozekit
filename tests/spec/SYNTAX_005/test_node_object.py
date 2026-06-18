"""SYNTAX-005: node must be an object, node.id unique per canvas."""
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

class TestSYNTAX005_Positive:
    def test_valid_nodes(self):
        assert 'SYNTAX-005' not in _ids(VALID)

class TestSYNTAX005_Negative:
    def test_non_object_node(self):
        assert 'SYNTAX-005' in _ids('nodes:\n  - "not-an-object"\nedges: []')
    def test_duplicate_id_same_canvas(self):
        t = 'nodes:\n  - id: "dup"\n    type: "1"\n    data: {}\n  - id: "dup"\n    type: "2"\n    data: {}\nedges: []\n'
        assert 'SYNTAX-005' in _ids(t)

class TestSYNTAX005_EdgeCases:
    def test_same_id_in_subcanvas_no_conflict(self):
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "loop-1"\n    type: "21"\n    data:\n      nodeMeta:\n        title: "Loop"\n'
            '    blocks:\n      - id: "900001"\n        type: "2"\n        data:\n          nodeMeta:\n            title: "InnerEnd"\n'
            '    edges: []\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "loop-1"\n  - sourceNodeID: "loop-1"\n    targetNodeID: "900001"\n'
        )
        assert 'SYNTAX-005' not in _ids(t)
