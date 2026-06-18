"""BE-010: If node must have both branch ports."""
from __future__ import annotations
from tests.conftest import compile_text

def _be_ids(t):
    return [d.rule_id for d in compile_text(t).diagnostics if d.rule_id.startswith('SEMANTIC-BE')]

_IF_BASE = (
    'nodes:\n'
    '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
    '  - id: "if-1"\n    type: "8"\n    data:\n      nodeMeta:\n        title: "If"\n'
    '      inputs:\n        branches:\n          - branchKey: "true"\n            condition: {}\n          - branchKey: "false"\n            condition: {}\n'
    '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
    'edges:\n'
    '  - sourceNodeID: "100001"\n    targetNodeID: "if-1"\n'
    '  - sourceNodeID: "if-1"\n    sourcePortID: "true"\n    targetNodeID: "900001"\n'
    '  - sourceNodeID: "if-1"\n    sourcePortID: "false"\n    targetNodeID: "900001"\n'
)

class TestBE010_Positive:
    def test_if_with_both_branches(self):
        assert 'SEMANTIC-BE-010' not in _be_ids(_IF_BASE)

class TestBE010_Negative:
    def test_if_missing_false_branch(self):
        t = _IF_BASE.replace(
            '  - sourceNodeID: "if-1"\n    sourcePortID: "false"\n    targetNodeID: "900001"\n', ''
        )
        assert 'SEMANTIC-BE-010' in _be_ids(t)
