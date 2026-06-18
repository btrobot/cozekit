"""BE-016: nested composite nodes require live validation."""
from __future__ import annotations

from tests.conftest import compile_text


def _be016_ids(t):
    return [d.rule_id for d in compile_text(t).diagnostics if d.rule_id == 'SEMANTIC-BE-016']


class TestBE016_Positive:
    def test_single_level_composite(self):
        """Loop with code blocks (non-composite) → no BE-016."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "loop-1"\n    type: "21"\n    data:\n      nodeMeta:\n        title: "Loop"\n'
            '    blocks:\n'
            '      - id: "code-1"\n        type: "5"\n        data:\n          nodeMeta:\n            title: "Code"\n'
            '    edges: []\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "loop-1"\n  - sourceNodeID: "loop-1"\n    targetNodeID: "900001"\n'
        )
        assert 'SEMANTIC-BE-016' not in _be016_ids(t)


class TestBE016_Negative:
    def test_nested_composite_triggers(self):
        """Loop containing a loop in blocks → BE-016."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "loop-1"\n    type: "21"\n    data:\n      nodeMeta:\n        title: "Loop"\n'
            '    blocks:\n'
            '      - id: "inner-loop"\n        type: "21"\n        data:\n          nodeMeta:\n            title: "InnerLoop"\n'
            '    edges: []\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "loop-1"\n  - sourceNodeID: "loop-1"\n    targetNodeID: "900001"\n'
        )
        ids = _be016_ids(t)
        assert len(ids) >= 1
