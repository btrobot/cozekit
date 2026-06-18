"""FE-013: Output variable name validation.

Validates that output variable names:
  - Are non-empty
  - Match identifier format (letter/underscore start, alphanumeric/underscore/$ rest)
  - Are not reserved words (12 个: true, false, and, AND, or, OR, not, NOT, null, nil, If, Switch)
  - Have required `type` field
  - Are unique among siblings (SPEC-OUT-006)
  - Children are validated recursively

规则来源: coze-workflow-spec.md §2.4, §4.4.1, §4.4.2
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


# ── Positive ─────────────────────────────────────────────────────

class TestFE013_Positive:
    def test_valid_name(self):
        t = _make_workflow("        - name: result\n          type: string")
        assert 'SEMANTIC-FE-013' not in _fe013_ids(t)

    def test_underscore_start(self):
        t = _make_workflow("        - name: _private\n          type: string")
        assert 'SEMANTIC-FE-013' not in _fe013_ids(t)

    def test_alphanumeric_underscore(self):
        t = _make_workflow("        - name: output_1\n          type: string")
        assert 'SEMANTIC-FE-013' not in _fe013_ids(t)

    def test_with_children(self):
        t = _make_workflow(
            "        - name: data\n          type: object\n"
            "          children:\n"
            "            - name: field1\n              type: string\n"
            "            - name: field2\n              type: integer"
        )
        assert 'SEMANTIC-FE-013' not in _fe013_ids(t)

    def test_empty_outputs_no_error(self):
        t = _make_workflow("        []")
        assert 'SEMANTIC-FE-013' not in _fe013_ids(t)

    def test_no_outputs_field_no_error(self):
        t = """nodes:
  - id: '100001'
    type: '1'
    data:
      nodeMeta:
        title: Start
  - id: '900001'
    type: '2'
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: '100001'
    targetNodeID: '900001'
"""
        assert 'SEMANTIC-FE-013' not in _fe013_ids(t)

    def test_dollar_in_name(self):
        """Name with $ in continue position → valid per regex ^[a-zA-Z_][a-zA-Z_$0-9]*$."""
        t = _make_workflow("        - name: my$var\n          type: string")
        assert 'SEMANTIC-FE-013' not in _fe013_ids(t)

    def test_camel_case_name(self):
        """CamelCase name → valid."""
        t = _make_workflow("        - name: myOutputVar\n          type: string")
        assert 'SEMANTIC-FE-013' not in _fe013_ids(t)

    def test_uppercase_name(self):
        """All uppercase name → valid."""
        t = _make_workflow("        - name: RESULT\n          type: string")
        assert 'SEMANTIC-FE-013' not in _fe013_ids(t)

    def test_lowercase_reserved_not_in_list(self):
        """Lowercase 'switch' is not a reserved word (only 'Switch' is)."""
        t = _make_workflow("        - name: switch\n          type: string")
        assert 'SEMANTIC-FE-013' not in _fe013_ids(t)

    def test_lowercase_reserved_not_in_list_if(self):
        """Lowercase 'if' is not a reserved word (only 'If' is)."""
        t = _make_workflow("        - name: if\n          type: string")
        assert 'SEMANTIC-FE-013' not in _fe013_ids(t)


# ── Negative: Reserved Words ─────────────────────────────────────

class TestFE013_ReservedWords:
    """All 12 reserved words must be rejected."""

    def test_reserved_word_true(self):
        t = _make_workflow("        - name: true\n          type: boolean")
        assert 'SEMANTIC-FE-013' in _fe013_ids(t)

    def test_reserved_word_false(self):
        t = _make_workflow("        - name: false\n          type: boolean")
        assert 'SEMANTIC-FE-013' in _fe013_ids(t)

    def test_reserved_word_and_lowercase(self):
        t = _make_workflow("        - name: and\n          type: string")
        assert 'SEMANTIC-FE-013' in _fe013_ids(t)

    def test_reserved_word_AND_uppercase(self):
        t = _make_workflow("        - name: AND\n          type: string")
        assert 'SEMANTIC-FE-013' in _fe013_ids(t)

    def test_reserved_word_or_lowercase(self):
        t = _make_workflow("        - name: or\n          type: string")
        assert 'SEMANTIC-FE-013' in _fe013_ids(t)

    def test_reserved_word_OR_uppercase(self):
        t = _make_workflow("        - name: OR\n          type: string")
        assert 'SEMANTIC-FE-013' in _fe013_ids(t)

    def test_reserved_word_not_lowercase(self):
        t = _make_workflow("        - name: not\n          type: string")
        assert 'SEMANTIC-FE-013' in _fe013_ids(t)

    def test_reserved_word_NOT_uppercase(self):
        t = _make_workflow("        - name: NOT\n          type: string")
        assert 'SEMANTIC-FE-013' in _fe013_ids(t)

    def test_reserved_word_null(self):
        t = _make_workflow("        - name: null\n          type: string")
        assert 'SEMANTIC-FE-013' in _fe013_ids(t)

    def test_reserved_word_nil(self):
        t = _make_workflow("        - name: nil\n          type: string")
        assert 'SEMANTIC-FE-013' in _fe013_ids(t)

    def test_reserved_word_If(self):
        t = _make_workflow("        - name: If\n          type: string")
        assert 'SEMANTIC-FE-013' in _fe013_ids(t)

    def test_reserved_word_Switch(self):
        t = _make_workflow("        - name: Switch\n          type: string")
        assert 'SEMANTIC-FE-013' in _fe013_ids(t)


# ── Negative: Format Violations ──────────────────────────────────

class TestFE013_FormatViolations:
    """Invalid identifier format → FE-013 error."""

    def test_empty_name(self):
        t = _make_workflow("        - name: ''\n          type: string")
        assert 'SEMANTIC-FE-013' in _fe013_ids(t)

    def test_starts_with_digit(self):
        t = _make_workflow("        - name: 123abc\n          type: string")
        assert 'SEMANTIC-FE-013' in _fe013_ids(t)

    def test_contains_hyphen(self):
        t = _make_workflow("        - name: my-var\n          type: string")
        assert 'SEMANTIC-FE-013' in _fe013_ids(t)

    def test_contains_dot(self):
        t = _make_workflow("        - name: my.var\n          type: string")
        assert 'SEMANTIC-FE-013' in _fe013_ids(t)

    def test_contains_space(self):
        t = _make_workflow("        - name: my output\n          type: string")
        assert 'SEMANTIC-FE-013' in _fe013_ids(t)

    def test_contains_at_sign(self):
        t = _make_workflow("        - name: my@var\n          type: string")
        assert 'SEMANTIC-FE-013' in _fe013_ids(t)


# ── Negative: Children Recursive ─────────────────────────────────

class TestFE013_Children:
    """Children output names are validated recursively."""

    def test_child_invalid_name(self):
        t = _make_workflow(
            "        - name: data\n          type: object\n"
            "          children:\n"
            "            - name: valid\n              type: string\n"
            "            - name: null\n              type: string"
        )
        ids = _fe013_ids(t)
        assert len(ids) == 1

    def test_multiple_invalid(self):
        t = _make_workflow(
            "        - name: true\n          type: boolean\n"
            "        - name: 123bad\n          type: string"
        )
        ids = _fe013_ids(t)
        assert len(ids) == 2

    def test_deeply_nested_invalid(self):
        """Invalid name at depth 2 → caught."""
        t = _make_workflow(
            "        - name: root\n          type: object\n"
            "          children:\n"
            "            - name: child\n              type: object\n"
            "              children:\n"
            "                - name: If\n                  type: string"
        )
        ids = _fe013_ids(t)
        assert len(ids) == 1


# ── Negative: Type Required ──────────────────────────────────────

class TestFE013_TypeRequired:
    """Output variable must declare type (§4.4.2)."""

    def test_missing_type(self):
        """Output without type field → should error."""
        t = _make_workflow("        - name: result")
        ids = _fe013_ids(t)
        assert len(ids) >= 1


# ── Negative: Uniqueness (SPEC-OUT-006) ──────────────────────────

class TestFE013_Uniqueness:
    """Sibling output names must be unique (SPEC-OUT-006)."""

    def test_duplicate_sibling_names(self):
        """Two outputs with same name → should error."""
        t = _make_workflow(
            "        - name: result\n          type: string\n"
            "        - name: result\n          type: integer"
        )
        ids = _fe013_ids(t)
        assert len(ids) >= 1

    def test_duplicate_children_names(self):
        """Children with duplicate names → should error."""
        t = _make_workflow(
            "        - name: data\n          type: object\n"
            "          children:\n"
            "            - name: field1\n              type: string\n"
            "            - name: field1\n              type: integer"
        )
        ids = _fe013_ids(t)
        assert len(ids) >= 1
