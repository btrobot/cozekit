"""BE-003: edge source/target nodes must exist."""
from __future__ import annotations

from tests.conftest import compile_text


def _be003_ids(t):
    return [d.rule_id for d in compile_text(t).diagnostics if d.rule_id == 'SEMANTIC-BE-003']


class TestBE003_Positive:
    def test_all_edges_valid(self):
        """All edges reference existing nodes → no BE-003."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "900001"\n'
        )
        assert 'SEMANTIC-BE-003' not in _be003_ids(t)


class TestBE003_Negative:
    def test_missing_source_node(self):
        """Edge references non-existent source → BE-003."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "ghost"\n    targetNodeID: "900001"\n'
        )
        ids = _be003_ids(t)
        assert len(ids) == 1

    def test_missing_target_node(self):
        """Edge references non-existent target → BE-003."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "ghost"\n'
        )
        ids = _be003_ids(t)
        assert len(ids) == 1

    def test_both_endpoints_missing(self):
        """Edge with both endpoints invalid → two BE-003 diagnostics."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "a"\n    targetNodeID: "b"\n'
        )
        ids = _be003_ids(t)
        assert len(ids) == 2
