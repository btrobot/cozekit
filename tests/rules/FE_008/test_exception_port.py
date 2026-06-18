"""FE-008: exception port connectivity."""
from __future__ import annotations
from tests.conftest import compile_text

def _fe_ids(t):
    return [d.rule_id for d in compile_text(t).diagnostics if d.rule_id.startswith('SEMANTIC-FE')]

class TestFE008_Positive:
    def test_no_exception_config(self):
        assert 'SEMANTIC-FE-008' not in _fe_ids(
            'nodes:\n  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "900001"\n'
        )
