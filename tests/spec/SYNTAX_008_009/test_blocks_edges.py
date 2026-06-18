"""SYNTAX-008/009: blocks/edges validation for composite nodes."""
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

class TestSYNTAX008_009_Positive:
    def test_composite_node_with_blocks(self):
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "loop-1"\n    type: "21"\n    data:\n      nodeMeta:\n        title: "Loop"\n'
            '    blocks:\n      - id: "inner"\n        type: "5"\n        data:\n          nodeMeta:\n            title: "Code"\n'
            '    edges: []\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "loop-1"\n  - sourceNodeID: "loop-1"\n    targetNodeID: "900001"\n'
        )
        ids = _ids(t)
        assert 'SYNTAX-008' not in ids

class TestSYNTAX008_009_Negative:
    def test_non_composite_with_blocks(self):
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "n1"\n    type: "5"\n    data:\n      nodeMeta:\n        title: "Code"\n'
            '    blocks:\n      - id: "inner"\n        type: "5"\n        data: {}\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "n1"\n  - sourceNodeID: "n1"\n    targetNodeID: "900001"\n'
        )
        assert 'SYNTAX-008' in _ids(t)


class TestSYNTAX009_Negative:
    def test_nested_edges_without_blocks_warns(self):
        """Node has edges key but no blocks → SYNTAX-009 warning."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "loop-1"\n    type: "21"\n    data:\n      nodeMeta:\n        title: "Loop"\n'
            '    edges:\n      - sourceNodeID: "inner-a"\n        targetNodeID: "inner-b"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "loop-1"\n  - sourceNodeID: "loop-1"\n    targetNodeID: "900001"\n'
        )
        assert 'SYNTAX-009' in _ids(t)

class TestSYNTAX009_Positive:
    def test_composite_with_blocks_and_edges_no_warning(self):
        """Composite node with both blocks and edges → no SYNTAX-009."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "loop-1"\n    type: "21"\n    data:\n      nodeMeta:\n        title: "Loop"\n'
            '    blocks:\n      - id: "inner"\n        type: "5"\n        data:\n          nodeMeta:\n            title: "Code"\n'
            '    edges:\n      - sourceNodeID: "inner"\n        targetNodeID: "inner"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "loop-1"\n  - sourceNodeID: "loop-1"\n    targetNodeID: "900001"\n'
        )
        assert 'SYNTAX-009' not in _ids(t)
