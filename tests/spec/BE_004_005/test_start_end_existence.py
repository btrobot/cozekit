"""BE-004/005: start and end nodes must exist."""
from __future__ import annotations
from tests.conftest import compile_text

def _be_ids(t):
    return [d.rule_id for d in compile_text(t).diagnostics if d.rule_id.startswith('SEMANTIC-BE')]

class TestBE004_005_Positive:
    def test_start_end_exist(self):
        ids = _be_ids(
            'nodes:\n  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "900001"\n'
        )
        assert 'SEMANTIC-BE-004' not in ids
        assert 'SEMANTIC-BE-005' not in ids

class TestBE004_005_Negative:
    def test_no_start(self):
        ids = _be_ids('nodes:\n  - id: "900001"\n    type: "2"\n    data: {}\nedges: []\n')
        assert 'SEMANTIC-BE-004' in ids
    def test_no_end(self):
        ids = _be_ids('nodes:\n  - id: "100001"\n    type: "1"\n    data: {}\nedges: []\n')
        assert 'SEMANTIC-BE-005' in ids
