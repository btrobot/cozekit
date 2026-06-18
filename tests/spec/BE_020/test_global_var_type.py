"""BE-020: global variable type validation."""
from __future__ import annotations

from tests.conftest import compile_text


def _be020_ids(t):
    return [d.rule_id for d in compile_text(t).diagnostics if d.rule_id == 'SEMANTIC-BE-020']


class TestBE020_Positive:
    def test_variable_with_type(self):
        """Variable node (type 11) with type specified → no BE-020."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "var-1"\n    type: "11"\n    data:\n      nodeMeta:\n        title: "Var"\n'
            '      inputs:\n        name: "myVar"\n        type: "string"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "var-1"\n  - sourceNodeID: "var-1"\n    targetNodeID: "900001"\n'
        )
        assert 'SEMANTIC-BE-020' not in _be020_ids(t)


class TestBE020_Negative:
    def test_variable_without_type(self):
        """Variable node (type 11) without type → BE-020."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "var-1"\n    type: "11"\n    data:\n      nodeMeta:\n        title: "Var"\n'
            '      inputs:\n        name: "myVar"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "var-1"\n  - sourceNodeID: "var-1"\n    targetNodeID: "900001"\n'
        )
        ids = _be020_ids(t)
        assert len(ids) >= 1
