"""Condition operator validation — all 16 operators, unary rules, right-value constraints.

Covers:
  - SPEC-COND-ENUM-001: all 16 ConditionType operators
  - SPEC-COND-ENUM-002: unary operators (9,10,11,12) do not require right
  - SPEC-COND-ENUM-003: length comparison operators (3,4,5,6)
  - SPEC-COND-001: left operand required
  - SPEC-COND-002: operator required
  - SPEC-COND-003: right operand required for binary operators

规则来源: specialized-rules.json, coze-workflow-spec.md §3.4.1
"""
from __future__ import annotations

import pytest

from tests.conftest import compile_text


def _fe001_messages(t):
    return [d.message for d in compile_text(t).diagnostics if d.rule_id == 'SEMANTIC-FE-001']


def _make_if_yaml(conditions_yaml: str) -> str:
    """Build a minimal workflow with an If node containing given conditions."""
    return f"""nodes:
  - id: '100001'
    type: '1'
    data:
      nodeMeta:
        title: Start
  - id: 'if-1'
    type: '8'
    data:
      nodeMeta:
        title: Condition
      inputs:
        branches:
          - branchKey: 'true'
            condition:
              logic: and
              conditions:
{conditions_yaml}
          - branchKey: 'false'
            condition: {{}}
  - id: '900001'
    type: '2'
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: '100001'
    targetNodeID: 'if-1'
  - sourceNodeID: 'if-1'
    sourcePortID: 'true'
    targetNodeID: '900001'
  - sourceNodeID: 'if-1'
    sourcePortID: 'false'
    targetNodeID: '900001'
"""


def _valid_binary_cond(op: str) -> str:
    """Generate a valid binary condition YAML block for operator `op`."""
    return (
        f"                - left:\n"
        f"                    type: ref\n"
        f"                    content:\n"
        f"                      source: block-output\n"
        f"                      blockID: '100001'\n"
        f"                      name: 'input_1'\n"
        f"                  operator: '{op}'\n"
        f"                  right:\n"
        f"                    type: literal\n"
        f"                    content: 'hello'\n"
    )


def _valid_unary_cond(op: str) -> str:
    """Generate a valid unary condition YAML block for operator `op`."""
    return (
        f"                - left:\n"
        f"                    type: ref\n"
        f"                    content:\n"
        f"                      source: block-output\n"
        f"                      blockID: '100001'\n"
        f"                      name: 'input_1'\n"
        f"                  operator: '{op}'\n"
    )


# All 16 operator IDs
BINARY_OPERATORS = ['1', '2', '3', '4', '5', '6', '7', '8', '13', '14', '15', '16']
UNARY_OPERATORS = ['9', '10', '11', '12']
ALL_OPERATORS = BINARY_OPERATORS + UNARY_OPERATORS


# ── Positive: All operators valid with correct structure ─────────

class TestConditionOperators_AllBinary_Positive:
    """All 12 binary operators with left + operator + right → no condition error."""

    @pytest.mark.parametrize('op', BINARY_OPERATORS, ids=[
        'Equal(1)', 'NotEqual(2)', 'LengthGt(3)', 'LengthGtEqual(4)',
        'LengthLt(5)', 'LengthLtEqual(6)', 'Contains(7)', 'NotContains(8)',
        'Gt(13)', 'GtEqual(14)', 'Lt(15)', 'LtEqual(16)',
    ])
    def test_binary_operator_valid(self, op):
        yaml = _make_if_yaml(_valid_binary_cond(op))
        errors = _fe001_messages(yaml)
        assert not any('If condition' in e for e in errors)


class TestConditionOperators_AllUnary_Positive:
    """All 4 unary operators without right → no condition error."""

    @pytest.mark.parametrize('op', UNARY_OPERATORS, ids=[
        'Null(9)', 'NotNull(10)', 'True(11)', 'False(12)',
    ])
    def test_unary_operator_valid(self, op):
        yaml = _make_if_yaml(_valid_unary_cond(op))
        errors = _fe001_messages(yaml)
        assert not any('If condition' in e for e in errors)


# ── Negative: Unary operators should NOT require right ───────────

class TestConditionOperators_UnaryNoRight:
    """Unary operators without right value → no error (right is disabled)."""

    def test_null_without_right(self):
        yaml = _make_if_yaml(_valid_unary_cond('9'))
        errors = _fe001_messages(yaml)
        assert not any('right operand' in e for e in errors)

    def test_notnull_without_right(self):
        yaml = _make_if_yaml(_valid_unary_cond('10'))
        errors = _fe001_messages(yaml)
        assert not any('right operand' in e for e in errors)

    def test_true_without_right(self):
        yaml = _make_if_yaml(_valid_unary_cond('11'))
        errors = _fe001_messages(yaml)
        assert not any('right operand' in e for e in errors)

    def test_false_without_right(self):
        yaml = _make_if_yaml(_valid_unary_cond('12'))
        errors = _fe001_messages(yaml)
        assert not any('right operand' in e for e in errors)


# ── Negative: Binary operators without right → error ─────────────

class TestConditionOperators_BinaryMissingRight:
    """Binary operator without right → right operand required error."""

    @pytest.mark.parametrize('op', BINARY_OPERATORS, ids=[
        'Equal(1)', 'NotEqual(2)', 'LengthGt(3)', 'LengthGtEqual(4)',
        'LengthLt(5)', 'LengthLtEqual(6)', 'Contains(7)', 'NotContains(8)',
        'Gt(13)', 'GtEqual(14)', 'Lt(15)', 'LtEqual(16)',
    ])
    def test_binary_missing_right(self, op):
        cond = (
            f"                - left:\n"
            f"                    type: ref\n"
            f"                    content:\n"
            f"                      source: block-output\n"
            f"                      blockID: '100001'\n"
            f"                      name: 'input_1'\n"
            f"                  operator: '{op}'\n"
        )
        yaml = _make_if_yaml(cond)
        errors = _fe001_messages(yaml)
        assert any('right operand is required' in e for e in errors)


# ── Negative: Missing left operand → error ───────────────────────

class TestConditionOperators_MissingLeft:
    """Missing left operand → error for any operator."""

    def test_binary_missing_left(self):
        cond = (
            "                - operator: '1'\n"
            "                  right:\n"
            "                    type: literal\n"
            "                    content: 'hello'\n"
        )
        yaml = _make_if_yaml(cond)
        errors = _fe001_messages(yaml)
        assert any('left operand is required' in e for e in errors)

    def test_unary_missing_left(self):
        cond = "                - operator: '9'\n"
        yaml = _make_if_yaml(cond)
        errors = _fe001_messages(yaml)
        assert any('left operand is required' in e for e in errors)


# ── Negative: Missing operator → error ───────────────────────────

class TestConditionOperators_MissingOperator:
    """Missing operator → error."""

    def test_missing_operator(self):
        cond = (
            "                - left:\n"
            "                    type: ref\n"
            "                    content:\n"
            "                      source: block-output\n"
            "                      blockID: '100001'\n"
            "                      name: 'input_1'\n"
            "                  right:\n"
            "                    type: literal\n"
            "                    content: 'hello'\n"
        )
        yaml = _make_if_yaml(cond)
        errors = _fe001_messages(yaml)
        assert any('operator is required' in e for e in errors)


# ── Edge Cases ───────────────────────────────────────────────────

class TestConditionOperators_EdgeCases:
    """Edge cases for condition validation."""

    def test_mixed_unary_and_binary_conditions(self):
        """Mix of unary (Null) and binary (Equal) in same branch → no error."""
        conds = _valid_unary_cond('9') + _valid_binary_cond('1')
        yaml = _make_if_yaml(conds)
        errors = _fe001_messages(yaml)
        assert not any('If condition' in e for e in errors)

    def test_multiple_binary_conditions(self):
        """Two binary conditions in same branch → no error."""
        conds = _valid_binary_cond('1') + _valid_binary_cond('13')
        yaml = _make_if_yaml(conds)
        errors = _fe001_messages(yaml)
        assert not any('If condition' in e for e in errors)

    def test_length_operators_with_literal_right(self):
        """Length operators (3-6) with literal right value → valid."""
        for op in ['3', '4', '5', '6']:
            yaml = _make_if_yaml(_valid_binary_cond(op))
            errors = _fe001_messages(yaml)
            assert not any('If condition' in e for e in errors)

    def test_contains_operator_valid(self):
        """Contains operator (7) with ref left + literal right → valid."""
        yaml = _make_if_yaml(_valid_binary_cond('7'))
        errors = _fe001_messages(yaml)
        assert not any('If condition' in e for e in errors)

    def test_empty_conditions_list(self):
        """Empty conditions list → no condition errors."""
        yaml = _make_if_yaml('')
        errors = _fe001_messages(yaml)
        assert not any('If condition' in e for e in errors)

    def test_one_valid_one_invalid_conditions(self):
        """One valid binary + one missing left → error for missing left only."""
        conds = _valid_binary_cond('1') + (
            "                - operator: '1'\n"
            "                  right:\n"
            "                    type: literal\n"
            "                    content: 'hello'\n"
        )
        yaml = _make_if_yaml(conds)
        errors = _fe001_messages(yaml)
        assert any('left operand is required' in e for e in errors)
