"""SYNTAX-002/003: nodes and edges are required lists.

Implementation: passes/syntax/syntax_pass.py

SYNTAX-002 fires when no nodes are found in any canvas.
SYNTAX-003 fires when no edges are found in any canvas.

Tests expanded to cover:
  - Valid workflow with both nodes and edges
  - Missing nodes key entirely
  - Missing edges key entirely
  - nodes/edges as non-list types
  - nodes present but empty list (no edges)
"""

from __future__ import annotations
from tests.conftest import compile_text

VALID = (
    'nodes:\n'
    '  - id: "100001"\n'
    '    type: "1"\n'
    '    data:\n'
    '      nodeMeta:\n'
    '        title: "Start"\n'
    '  - id: "900001"\n'
    '    type: "2"\n'
    '    data:\n'
    '      nodeMeta:\n'
    '        title: "End"\n'
    'edges:\n'
    '  - sourceNodeID: "100001"\n'
    '    targetNodeID: "900001"\n'
)


def _ids(t):
    return [d.rule_id for d in compile_text(t).diagnostics if d.rule_id.startswith('SYNTAX')]


# ── Positive ─────────────────────────────────────────────────────

class TestSYNTAX002_003_Positive:
    """Valid workflow with nodes and edges → no SYNTAX-002/003."""

    def test_has_nodes_and_edges(self):
        ids = _ids(VALID)
        assert 'SYNTAX-002' not in ids
        assert 'SYNTAX-003' not in ids

    def test_multiple_nodes_and_edges(self):
        """Multiple nodes and edges → no SYNTAX-002/003."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "n1"\n    type: "3"\n    data:\n      nodeMeta:\n        title: "LLM"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n'
            '  - sourceNodeID: "100001"\n    targetNodeID: "n1"\n'
            '  - sourceNodeID: "n1"\n    targetNodeID: "900001"\n'
        )
        ids = _ids(t)
        assert 'SYNTAX-002' not in ids
        assert 'SYNTAX-003' not in ids


# ── Negative ─────────────────────────────────────────────────────

class TestSYNTAX002_003_Negative:
    """Missing or malformed nodes/edges → SYNTAX-002/003."""

    def test_missing_nodes_key(self):
        """No nodes key at all → SYNTAX-002."""
        assert 'SYNTAX-002' in _ids('{}')

    def test_missing_edges_key(self):
        """Nodes present but no edges key → SYNTAX-003."""
        t = 'nodes:\n  - id: "100001"\n    type: "1"\n    data: {}'
        assert 'SYNTAX-003' in _ids(t)

    def test_nodes_not_list(self):
        """nodes as string → SYNTAX-002."""
        assert 'SYNTAX-002' in _ids('nodes: "bad"\nedges: []')

    def test_edges_not_list(self):
        """edges as string → SYNTAX-003."""
        assert 'SYNTAX-003' in _ids('nodes: []\nedges: "bad"')

    def test_nodes_empty_list(self):
        """nodes=[] → SYNTAX-002."""
        assert 'SYNTAX-002' in _ids('nodes: []\nedges: []')

    def test_edges_empty_list(self):
        """nodes present but edges=[] → SYNTAX-003."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            'edges: []'
        )
        assert 'SYNTAX-003' in _ids(t)
