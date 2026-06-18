"""FE-009/010/011: title required, max length, unique."""
from __future__ import annotations
from tests.conftest import compile_text

def _fe_ids(t):
    return sorted(d.rule_id for d in compile_text(t).diagnostics if d.rule_id.startswith('SEMANTIC-FE'))

VALID = (
    'nodes:\n'
    '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
    '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
    'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "900001"\n'
)

class TestFE009_010_011_Positive:
    def test_clean_titles(self):
        ids = _fe_ids(VALID)
        assert 'SEMANTIC-FE-009' not in ids
        assert 'SEMANTIC-FE-010' not in ids
        assert 'SEMANTIC-FE-011' not in ids

class TestFE009_010_011_Negative:
    def test_empty_title(self):
        assert 'SEMANTIC-FE-009' in _fe_ids(
            'nodes:\n  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: ""\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "900001"\n'
        )

    def test_long_title(self):
        assert 'SEMANTIC-FE-010' in _fe_ids(
            'nodes:\n  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "n1"\n    type: "3"\n    data:\n      nodeMeta:\n        title: "' + 'x' * 64 + '"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "n1"\n  - sourceNodeID: "n1"\n    targetNodeID: "900001"\n'
        )

    def test_duplicate_title(self):
        ids = _fe_ids(
            'nodes:\n  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "n1"\n    type: "3"\n    data:\n      nodeMeta:\n        title: "dup"\n'
            '  - id: "n2"\n    type: "5"\n    data:\n      nodeMeta:\n        title: "dup"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "n1"\n  - sourceNodeID: "n1"\n    targetNodeID: "n2"\n  - sourceNodeID: "n2"\n    targetNodeID: "900001"\n'
        )
        assert ids.count('SEMANTIC-FE-011') == 2
