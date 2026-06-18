"""PORTABILITY-009: break/continue outside loop."""
from __future__ import annotations
from tests.conftest import compile_text

def _port_ids(t):
    return [d.rule_id for d in compile_text(t).diagnostics if d.rule_id.startswith('PORTABILITY')]

class TestPORT009_Positive:
    def test_break_inside_loop(self):
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "loop-1"\n    type: "21"\n    data:\n      nodeMeta:\n        title: "Loop"\n'
            '    blocks:\n      - id: "brk"\n        type: "19"\n        data:\n          nodeMeta:\n            title: "Break"\n'
            '    edges: []\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "loop-1"\n  - sourceNodeID: "loop-1"\n    targetNodeID: "900001"\n'
        )
        assert 'PORTABILITY-009' not in _port_ids(t)

class TestPORT009_Negative:
    def test_break_outside_loop(self):
        assert 'PORTABILITY-009' in _port_ids(
            'nodes:\n  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "brk"\n    type: "19"\n    data:\n      nodeMeta:\n        title: "Break"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "brk"\n  - sourceNodeID: "brk"\n    targetNodeID: "900001"\n'
        )
