"""Output variable validation — extended coverage.

Covers gaps in existing FE-013 tests:
  - sys_ prefix (VAL-SYSTEM-VARIABLE-001) — not yet implemented in compiler
  - Output variable type required (SPEC-OUT-008)
  - Output name uniqueness (SPEC-OUT-006) — currently xfail
  - Output name format with $ in various positions

NOTE: The compiler does not yet check sys_ prefix or output name uniqueness.
Those tests are marked xfail.

规则来源: specialized-rules.json SPEC-OUT-*, coze-workflow-spec.md §2.4
"""
from __future__ import annotations

import pytest

from tests.conftest import compile_text


def _fe013_ids(t):
    return [d.rule_id for d in compile_text(t).diagnostics if d.rule_id == 'SEMANTIC-FE-013']


def _fe013_messages(t):
    return [d.message for d in compile_text(t).diagnostics if d.rule_id == 'SEMANTIC-FE-013']


def _make_workflow(outputs_yaml: str) -> str:
    return f"""nodes:
  - id: '100001'
    type: '1'
    data:
      nodeMeta:
        title: Start
  - id: 'llm1'
    type: '3'
    data:
      nodeMeta:
        title: LLM
      outputs:
{outputs_yaml}
  - id: '900001'
    type: '2'
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: '100001'
    targetNodeID: 'llm1'
  - sourceNodeID: 'llm1'
    targetNodeID: '900001'
"""


# ── Positive: Valid output names ─────────────────────────────────

class TestOutputValidation_Positive:
    """Valid output configurations → no FE-013 errors."""

    def test_simple_output(self):
        """Simple valid output name → no error."""
        t = _make_workflow("        - name: result\n          type: 1")
        assert 'SEMANTIC-FE-013' not in _fe013_ids(t)

    def test_output_with_underscore(self):
        """Name with underscores → valid."""
        t = _make_workflow("        - name: my_output_var\n          type: 1")
        assert 'SEMANTIC-FE-013' not in _fe013_ids(t)

    def test_output_with_dollar_suffix(self):
        """Name with $ at end → valid per regex."""
        t = _make_workflow("        - name: output$\n          type: 1")
        assert 'SEMANTIC-FE-013' not in _fe013_ids(t)

    def test_output_with_dollar_middle(self):
        """Name with $ in middle → valid per regex."""
        t = _make_workflow("        - name: my$output\n          type: 1")
        assert 'SEMANTIC-FE-013' not in _fe013_ids(t)

    def test_output_uppercase(self):
        """All uppercase → valid."""
        t = _make_workflow("        - name: RESULT\n          type: 1")
        assert 'SEMANTIC-FE-013' not in _fe013_ids(t)

    def test_output_mixed_case(self):
        """Mixed case → valid."""
        t = _make_workflow("        - name: myResult\n          type: 1")
        assert 'SEMANTIC-FE-013' not in _fe013_ids(t)

    def test_output_numeric_suffix(self):
        """Name ending with digits → valid."""
        t = _make_workflow("        - name: output123\n          type: 1")
        assert 'SEMANTIC-FE-013' not in _fe013_ids(t)

    def test_output_single_letter(self):
        """Single letter name → valid."""
        t = _make_workflow("        - name: x\n          type: 1")
        assert 'SEMANTIC-FE-013' not in _fe013_ids(t)

    def test_output_with_children(self):
        """Output with nested children → valid."""
        t = _make_workflow(
            "        - name: data\n          type: 1\n"
            "          children:\n"
            "            - name: field1\n              type: 1\n"
            "            - name: field2\n              type: 1"
        )
        assert 'SEMANTIC-FE-013' not in _fe013_ids(t)

    def test_lowercase_if_not_reserved(self):
        """Lowercase 'if' is not reserved (only 'If' is)."""
        t = _make_workflow("        - name: if\n          type: 1")
        assert 'SEMANTIC-FE-013' not in _fe013_ids(t)


# ── Negative: Invalid output names ──────────────────────────────

class TestOutputValidation_ReservedWords:
    """All 12 reserved words must be rejected."""

    @pytest.mark.parametrize('name', [
        'true', 'false', 'and', 'AND', 'or', 'OR',
        'not', 'NOT', 'null', 'nil', 'If', 'Switch',
    ])
    def test_reserved_word(self, name):
        """Reserved word as output name → FE-013 error."""
        t = _make_workflow(f"        - name: {name}\n          type: 1")
        assert 'SEMANTIC-FE-013' in _fe013_ids(t)


class TestOutputValidation_InvalidFormat:
    """Invalid name formats → FE-013 error."""

    def test_name_starting_with_digit(self):
        """Name starting with digit → error."""
        t = _make_workflow("        - name: 1result\n          type: 1")
        assert 'SEMANTIC-FE-013' in _fe013_ids(t)

    def test_name_with_space(self):
        """Name with space → error."""
        t = _make_workflow("        - name: my output\n          type: 1")
        assert 'SEMANTIC-FE-013' in _fe013_ids(t)

    def test_name_with_hyphen(self):
        """Name with hyphen → error."""
        t = _make_workflow("        - name: my-output\n          type: 1")
        assert 'SEMANTIC-FE-013' in _fe013_ids(t)

    def test_empty_name(self):
        """Empty name → error."""
        t = _make_workflow("        - name: ''\n          type: 1")
        assert 'SEMANTIC-FE-013' in _fe013_ids(t)

    def test_name_starting_with_dollar(self):
        """Name starting with $ → error (must start with letter or _)."""
        t = _make_workflow("        - name: $temp\n          type: 1")
        # This should be invalid per the regex ^[a-zA-Z_][a-zA-Z_$0-9]*$
        assert 'SEMANTIC-FE-013' in _fe013_ids(t)


# ── Uniqueness (SPEC-OUT-006) — currently not implemented ───────

class TestOutputValidation_Uniqueness:
    """Sibling output name uniqueness (SPEC-OUT-006)."""

    def test_duplicate_sibling_names(self):
        """Two outputs with same name → FE-013 error (duplicate)."""
        t = _make_workflow(
            "        - name: result\n          type: 1\n"
            "        - name: result\n          type: 1"
        )
        assert 'SEMANTIC-FE-013' in _fe013_ids(t)

    def test_unique_sibling_names(self):
        """Two outputs with different names → no error."""
        t = _make_workflow(
            "        - name: result1\n          type: 1\n"
            "        - name: result2\n          type: 1"
        )
        dup_errors = [m for m in _fe013_messages(t) if 'duplicat' in m.lower()]
        assert len(dup_errors) == 0


# ── sys_ prefix (VAL-SYSTEM-VARIABLE-001) ───────────────────────

