"""BE-022: subworkflow live validation."""
from __future__ import annotations
from tests.conftest import compile_text

def _be_ids(t):
    return [d.rule_id for d in compile_text(t).diagnostics if d.rule_id.startswith('SEMANTIC-BE')]

class TestBE022_Negative:
    def test_subworkflow_fires_be022(self):
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "sw1"\n    type: "9"\n    data:\n      nodeMeta:\n        title: "SubWF"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "sw1"\n  - sourceNodeID: "sw1"\n    targetNodeID: "900001"\n'
        )
        assert 'SEMANTIC-BE-022' in _be_ids(t)
