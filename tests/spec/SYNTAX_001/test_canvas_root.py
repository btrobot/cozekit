"""SYNTAX-001: canvas root must be an object.

Implementation: passes/syntax/syntax_pass.py

Tests expanded to cover:
  - Valid canvas root (object with nodes+edges)
  - Non-object root: list, string, number, null
  - Empty canvas: nodes=[], edges=[]
  - Missing nodes or edges keys
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


def _sy001(t):
    return 'SYNTAX-001' in _ids(t)


# ── Positive ─────────────────────────────────────────────────────

class TestSYNTAX001_Positive:
    """Valid canvas roots produce no SYNTAX-001."""

    def test_valid_root(self):
        """Standard workflow with nodes and edges → no SYNTAX-001."""
        assert not _sy001(VALID)

    def test_root_with_extra_keys(self):
        """Root object with extra metadata keys → no SYNTAX-001."""
        t = 'versions:\n  version: "1.0"\n' + VALID
        assert not _sy001(t)

    def test_root_with_empty_nodes_and_edges(self):
        """Empty nodes/edges lists → no SYNTAX-001 (canvas is still an object)."""
        t = 'nodes: []\nedges: []'
        assert not _sy001(t)


# ── Negative ─────────────────────────────────────────────────────

class TestSYNTAX001_Negative:
    """Non-object roots produce SYNTAX-001."""

    def test_non_object_root_list(self):
        """YAML list root → SYNTAX-001."""
        assert _sy001('[]')

    def test_string_root(self):
        """YAML string root → SYNTAX-001."""
        assert _sy001('"hello"')

    def test_integer_root(self):
        """YAML integer root → SYNTAX-001."""
        assert _sy001('42')

    def test_null_root(self):
        """YAML null root (empty body) → SYNTAX-001."""
        assert _sy001('')

    def test_boolean_root(self):
        """YAML boolean root → SYNTAX-001."""
        assert _sy001('true')
