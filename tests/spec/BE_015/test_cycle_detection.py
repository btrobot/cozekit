"""BE-015: cycle detection in workflow graph."""
from __future__ import annotations
from tests.conftest import compile_text

def _be_ids(t):
    return [d.rule_id for d in compile_text(t).diagnostics if d.rule_id.startswith('SEMANTIC-BE')]

class TestBE015_Positive:
    def test_no_cycle(self):
        assert 'SEMANTIC-BE-015' not in _be_ids(
            'nodes:\n  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "900001"\n'
        )

class TestBE015_Negative:
    def test_cycle_detected(self):
        assert 'SEMANTIC-BE-015' in _be_ids(
            'nodes:\n  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "n1"\n    type: "5"\n    data:\n      nodeMeta:\n        title: "A"\n'
            '  - id: "n2"\n    type: "5"\n    data:\n      nodeMeta:\n        title: "B"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "n1"\n  - sourceNodeID: "n1"\n    targetNodeID: "n2"\n'
            '  - sourceNodeID: "n2"\n    targetNodeID: "n1"\n  - sourceNodeID: "n2"\n    targetNodeID: "900001"\n'
        )
