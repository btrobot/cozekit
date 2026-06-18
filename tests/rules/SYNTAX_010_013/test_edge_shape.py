"""SYNTAX-010/011: edge sourceNodeID / targetNodeID are required.

Implementation: passes/syntax/syntax_pass.py

SYNTAX-010: edge sourceNodeID is required.
SYNTAX-011: edge targetNodeID is required.

Tests expanded to cover:
  - Valid edge with both source and target
  - Missing source
  - Missing target
  - Missing both source and target
  - Empty string source/target
  - Multiple edges: one valid, one missing target
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
    return sorted(d.rule_id for d in compile_text(t).diagnostics if d.rule_id.startswith('SYNTAX'))


def _sy010(t):
    return 'SYNTAX-010' in _ids(t)


def _sy011(t):
    return 'SYNTAX-011' in _ids(t)


# ── Positive ─────────────────────────────────────────────────────

class TestSYNTAX010_011_Positive:
    """Valid edges produce no SYNTAX-010/011."""

    def test_valid_edges(self):
        ids = _ids(VALID)
        assert 'SYNTAX-010' not in ids
        assert 'SYNTAX-011' not in ids

    def test_edge_with_extra_fields(self):
        """Edge with sourcePortID and other metadata → no errors."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n'
            '  - sourceNodeID: "100001"\n    targetNodeID: "900001"\n    sourcePortID: "default"\n'
        )
        ids = _ids(t)
        assert 'SYNTAX-010' not in ids
        assert 'SYNTAX-011' not in ids


# ── Negative ─────────────────────────────────────────────────────

class TestSYNTAX010_Negative:
    """Missing sourceNodeID → SYNTAX-010."""

    def test_missing_source(self):
        t = 'nodes:\n  - id: "100001"\n    type: "1"\n    data: {}\nedges:\n  - targetNodeID: "100001"\n'
        assert _sy010(t)

    def test_empty_source(self):
        """Empty string sourceNodeID → SYNTAX-010."""
        t = 'nodes:\n  - id: "100001"\n    type: "1"\n    data: {}\nedges:\n  - sourceNodeID: ""\n    targetNodeID: "100001"\n'
        assert _sy010(t)


class TestSYNTAX011_Negative:
    """Missing targetNodeID → SYNTAX-011."""

    def test_missing_target(self):
        t = 'nodes:\n  - id: "100001"\n    type: "1"\n    data: {}\nedges:\n  - sourceNodeID: "100001"\n'
        assert _sy011(t)

    def test_empty_target(self):
        """Empty string targetNodeID → SYNTAX-011."""
        t = 'nodes:\n  - id: "100001"\n    type: "1"\n    data: {}\nedges:\n  - sourceNodeID: "100001"\n    targetNodeID: ""\n'
        assert _sy011(t)


class TestSYNTAX010_011_EdgeCases:
    """Edge cases for edge shape validation."""

    def test_missing_both_source_and_target(self):
        """Edge missing both source and target → both SYNTAX-010 and SYNTAX-011."""
        ids = _ids('nodes:\n  - id: "n1"\n    type: "1"\n    data: {}\nedges:\n  - sourcePortID: "default"\n')
        assert 'SYNTAX-010' in ids
        assert 'SYNTAX-011' in ids

    def test_multiple_edges_one_missing_target(self):
        """Two edges: one valid, one missing target → SYNTAX-011 only once for the bad edge."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n'
            '  - sourceNodeID: "100001"\n    targetNodeID: "900001"\n'
            '  - sourceNodeID: "100001"\n'
        )
        assert _sy011(t)
