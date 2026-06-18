"""SYNTAX-012: edges from branch-capable nodes should have sourcePortID.

Implementation: passes/syntax/syntax_pass.py

Tests expanded to cover:
  - If-node edge with sourcePortID → no warning
  - Normal node edge without sourcePortID → no warning
  - If-node edge without sourcePortID → warning
  - Intent-node edge without sourcePortID → warning
  - Multiple branch edges, one with and one without sourcePortID
"""

from __future__ import annotations
from tests.conftest import compile_text


def _ids(t):
    return [d.rule_id for d in compile_text(t).diagnostics if d.rule_id == 'SYNTAX-012']


# ── YAML templates ──────────────────────────────────────────────

_IF_WITH_BRANCHES = (
    'nodes:\n'
    '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
    '  - id: "if-1"\n    type: "8"\n    data:\n'
    '      nodeMeta:\n        title: "If"\n'
    '      inputs:\n'
    '        branches:\n'
    '          - id: "true"\n            branchKey: "true"\n'
    '          - id: "false"\n            branchKey: "false"\n'
    '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
)

_INTENT_WITH_BRANCHES = (
    'nodes:\n'
    '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
    '  - id: "intent-1"\n    type: "22"\n    data:\n'
    '      nodeMeta:\n        title: "Intent"\n'
    '      inputs:\n'
    '        inputParameters:\n'
    '          - name: query\n'
    '            input:\n'
    '              type: literal\n'
    '              value:\n'
    '                type: literal\n'
    '                content: "test"\n'
    '        branches:\n'
    '          - id: "intent-1"\n            branchKey: "intent_1"\n'
    '          - id: "other"\n            branchKey: "other"\n'
    '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
)


# ── Positive ─────────────────────────────────────────────────────

class TestSYNTAX012_Positive:
    """Valid branch edges produce no SYNTAX-012."""

    def test_branch_edge_with_source_port_id(self):
        """If-node edge with sourcePortID → no SYNTAX-012."""
        t = (
            _IF_WITH_BRANCHES +
            'edges:\n'
            '  - sourceNodeID: "100001"\n    targetNodeID: "if-1"\n'
            '  - sourceNodeID: "if-1"\n    targetNodeID: "900001"\n    sourcePortID: "true"\n'
        )
        assert 'SYNTAX-012' not in _ids(t)

    def test_non_branch_edge_without_port_id(self):
        """Normal node edge without sourcePortID → no SYNTAX-012."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "900001"\n'
        )
        assert 'SYNTAX-012' not in _ids(t)

    def test_both_branch_edges_with_port_id(self):
        """Both true and false edges with sourcePortID → no SYNTAX-012."""
        t = (
            _IF_WITH_BRANCHES +
            'edges:\n'
            '  - sourceNodeID: "100001"\n    targetNodeID: "if-1"\n'
            '  - sourceNodeID: "if-1"\n    targetNodeID: "900001"\n    sourcePortID: "true"\n'
            '  - sourceNodeID: "if-1"\n    targetNodeID: "900001"\n    sourcePortID: "false"\n'
        )
        assert 'SYNTAX-012' not in _ids(t)


# ── Negative ─────────────────────────────────────────────────────

class TestSYNTAX012_Negative:
    """Branch edge without sourcePortID → SYNTAX-012."""

    def test_if_edge_without_source_port_id(self):
        """If-node with branches but edge without sourcePortID → SYNTAX-012."""
        t = (
            _IF_WITH_BRANCHES +
            'edges:\n'
            '  - sourceNodeID: "100001"\n    targetNodeID: "if-1"\n'
            '  - sourceNodeID: "if-1"\n    targetNodeID: "900001"\n'
        )
        assert len(_ids(t)) >= 1

    def test_intent_edge_without_source_port_id(self):
        """Intent-node with branches but edge without sourcePortID → SYNTAX-012."""
        t = (
            _INTENT_WITH_BRANCHES +
            'edges:\n'
            '  - sourceNodeID: "100001"\n    targetNodeID: "intent-1"\n'
            '  - sourceNodeID: "intent-1"\n    targetNodeID: "900001"\n'
        )
        assert len(_ids(t)) >= 1


class TestSYNTAX012_EdgeCases:
    """Edge cases for branch port validation."""

    def test_mixed_edges_one_with_one_without_port_id(self):
        """Two edges from If: one with sourcePortID, one without → one SYNTAX-012."""
        t = (
            _IF_WITH_BRANCHES +
            'edges:\n'
            '  - sourceNodeID: "100001"\n    targetNodeID: "if-1"\n'
            '  - sourceNodeID: "if-1"\n    targetNodeID: "900001"\n    sourcePortID: "true"\n'
            '  - sourceNodeID: "if-1"\n    targetNodeID: "900001"\n'
        )
        ids = _ids(t)
        assert len(ids) == 1
