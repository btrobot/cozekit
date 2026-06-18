"""PORTABILITY-011: subworkflow self-reference."""
from __future__ import annotations
from tests.conftest import compile_text

def _port_ids(t):
    return [d.rule_id for d in compile_text(t).diagnostics if d.rule_id.startswith('PORTABILITY')]

class TestPORT011_Positive:
    def test_no_subworkflow(self):
        assert 'PORTABILITY-011' not in _port_ids(
            'nodes:\n  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "900001"\n'
        )

class TestPORT011_Negative:
    def test_subworkflow_fires(self):
        assert 'PORTABILITY-011' in _port_ids(
            'nodes:\n  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "sw1"\n    type: "9"\n    data:\n      nodeMeta:\n        title: "SubWF"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "sw1"\n  - sourceNodeID: "sw1"\n    targetNodeID: "900001"\n'
        )
