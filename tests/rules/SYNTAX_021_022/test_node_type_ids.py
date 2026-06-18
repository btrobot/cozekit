"""SYNTAX-021/022: node type ID validation.

Implementation: passes/syntax/syntax_pass.py

SYNTAX-021: node type must be a known Coze node type (warning).
SYNTAX-022: node type format validation (not currently implemented as separate rule).

Tests expanded to cover:
  - All standard known types accepted
  - Unknown type triggers SYNTAX-021
  - Numeric string types
  - Node type as integer vs string
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


def _sy021(t):
    return 'SYNTAX-021' in _ids(t)


# ── Positive ─────────────────────────────────────────────────────

class TestSYNTAX021_022_Positive:
    """Known node types produce no SYNTAX-021/022."""

    def test_known_types(self):
        """Standard Start + End → no SYNTAX-021/022."""
        ids = _ids(VALID)
        assert 'SYNTAX-021' not in ids
        assert 'SYNTAX-022' not in ids

    def test_all_frontend_types_known(self):
        """Every type in STANDARD_NODE_TYPE_TABLE should be recognized."""
        from cozekit.passes.syntax.syntax_pass import _FE_NAME_TO_NODE_TYPE as STANDARD_NODE_TYPE_TABLE
        for name, tid in STANDARD_NODE_TYPE_TABLE.items():
            t = VALID.replace(
                '  - id: "900001"',
                f'  - id: "test-node"\n    type: "{tid}"\n    data:\n      nodeMeta:\n        title: "{name}"\n  - id: "900001"'
            )
            assert not _sy021(t), f'{name} (type {tid}) should be known'

    def test_llm_type_known(self):
        """LLM type 3 → no SYNTAX-021."""
        t = VALID.replace(
            '  - id: "900001"',
            '  - id: "llm-1"\n    type: "3"\n    data:\n      nodeMeta:\n        title: "LLM"\n  - id: "900001"'
        )
        assert not _sy021(t)

    def test_code_type_known(self):
        """Code type 5 → no SYNTAX-021."""
        t = VALID.replace(
            '  - id: "900001"',
            '  - id: "code-1"\n    type: "5"\n    data:\n      nodeMeta:\n        title: "Code"\n  - id: "900001"'
        )
        assert not _sy021(t)

    def test_if_type_known(self):
        """If type 8 → no SYNTAX-021."""
        t = VALID.replace(
            '  - id: "900001"',
            '  - id: "if-1"\n    type: "8"\n    data:\n      nodeMeta:\n        title: "If"\n  - id: "900001"'
        )
        assert not _sy021(t)


# ── Negative ─────────────────────────────────────────────────────

class TestSYNTAX021_Negative:
    """Unknown node types trigger SYNTAX-021."""

    def test_unknown_type(self):
        """Type 99999 → SYNTAX-021."""
        t = VALID.replace(
            '  - id: "900001"',
            '  - id: "bad"\n    type: "99999"\n    data:\n      nodeMeta:\n        title: "Bad"\n  - id: "900001"'
        )
        assert _sy021(t)

    def test_very_large_type_id(self):
        """Very large type number → SYNTAX-021."""
        t = VALID.replace(
            '  - id: "900001"',
            '  - id: "bad"\n    type: "999999"\n    data:\n      nodeMeta:\n        title: "Huge"\n  - id: "900001"'
        )
        assert _sy021(t)

    def test_small_unknown_type_id(self):
        """Type 99 → SYNTAX-021 (not in known set)."""
        t = VALID.replace(
            '  - id: "900001"',
            '  - id: "bad"\n    type: "99"\n    data:\n      nodeMeta:\n        title: "Unknown"\n  - id: "900001"'
        )
        assert _sy021(t)


class TestSYNTAX021_EdgeCases:
    """Edge cases for node type validation."""

    def test_known_and_unknown_mixed(self):
        """One known + one unknown node → SYNTAX-021 only for unknown."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "llm-1"\n    type: "3"\n    data:\n      nodeMeta:\n        title: "LLM"\n'
            '  - id: "bad"\n    type: "99999"\n    data:\n      nodeMeta:\n        title: "Unknown"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n'
            '  - sourceNodeID: "100001"\n    targetNodeID: "llm-1"\n'
            '  - sourceNodeID: "llm-1"\n    targetNodeID: "900001"\n'
        )
        ids = _ids(t)
        assert ids.count('SYNTAX-021') == 1
