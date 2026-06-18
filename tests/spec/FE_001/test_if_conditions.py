"""FE-001: If 节点 (type 8) 条件分支验证。

验证规则:
  - left 操作数必填
  - operator 必填
  - right 操作数: 二元运算符必填, 一元运算符 (Null/NotNull/True/False) 不需要

Tests cover:
  - Valid binary condition
  - Valid unary conditions (Null, NotNull, True, False)
  - Missing left operand
  - Missing operator
  - Missing right for binary operator
  - Unary without right (allowed)
  - Empty conditions list
  - Multiple conditions
"""
from __future__ import annotations

import pytest

from tests.conftest import compile_text


def _fe001_errors(yaml_text: str) -> list[str]:
    """Extract FE-001 diagnostics."""
    report = compile_text(yaml_text)
    return [
        d.message for d in report.diagnostics
        if d.rule_id == 'SEMANTIC-FE-001'
    ]


# ── YAML template ───────────────────────────────────────────────

_IF_YAML_TEMPLATE = """\
nodes:
  - id: '100001'
    type: '1'
    data:
      nodeMeta:
        title: Start
  - id: 'if-1'
    type: '8'
    data:
      nodeMeta:
        title: If
      inputs:
        branches:
          - branchKey: 'true'
            condition:
              logic: and
              conditions:
{conditions}
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


def _make_if_yaml(conditions_yaml: str) -> str:
    return _IF_YAML_TEMPLATE.format(conditions=conditions_yaml)


# ── Condition YAML fragments ────────────────────────────────────

_VALID_BINARY_CONDITION = """\
                - left:
                    type: ref
                    content:
                      source: block-output
                      blockID: '100001'
                      name: 'input_1'
                  operator: '1'
                  right:
                    type: literal
                    content: 'hello'
"""

_VALID_UNARY_NULL_CONDITION = """\
                - left:
                    type: ref
                    content:
                      source: block-output
                      blockID: '100001'
                      name: 'input_1'
                  operator: '9'
"""

_VALID_UNARY_NOT_NULL_CONDITION = """\
                - left:
                    type: ref
                    content:
                      source: block-output
                      blockID: '100001'
                      name: 'input_1'
                  operator: '10'
"""

_VALID_UNARY_TRUE_CONDITION = """\
                - left:
                    type: ref
                    content:
                      source: block-output
                      blockID: '100001'
                      name: 'input_1'
                  operator: '11'
"""

_VALID_UNARY_FALSE_CONDITION = """\
                - left:
                    type: ref
                    content:
                      source: block-output
                      blockID: '100001'
                      name: 'input_1'
                  operator: '12'
"""

_MISSING_LEFT_CONDITION = """\
                - operator: '1'
                  right:
                    type: literal
                    content: 'hello'
"""

_MISSING_OPERATOR_CONDITION = """\
                - left:
                    type: ref
                    content:
                      source: block-output
                      blockID: '100001'
                      name: 'input_1'
                  right:
                    type: literal
                    content: 'hello'
"""

_MISSING_RIGHT_BINARY_CONDITION = """\
                - left:
                    type: ref
                    content:
                      source: block-output
                      blockID: '100001'
                      name: 'input_1'
                  operator: '1'
"""


# ── Positive tests ──────────────────────────────────────────────

class TestIF001_Positive:
    """Valid if-node conditions → no FE-001 errors."""

    def test_valid_binary_condition(self):
        """Binary operator with left + operator + right → no error."""
        yaml = _make_if_yaml(_VALID_BINARY_CONDITION)
        errors = _fe001_errors(yaml)
        assert not any('If condition' in e for e in errors)

    def test_valid_unary_null(self):
        """Unary operator Null (9) without right → no error."""
        yaml = _make_if_yaml(_VALID_UNARY_NULL_CONDITION)
        errors = _fe001_errors(yaml)
        assert not any('If condition' in e for e in errors)

    def test_valid_unary_not_null(self):
        """Unary operator NotNull (10) without right → no error."""
        yaml = _make_if_yaml(_VALID_UNARY_NOT_NULL_CONDITION)
        errors = _fe001_errors(yaml)
        assert not any('If condition' in e for e in errors)

    def test_valid_unary_true(self):
        """Unary operator True (11) without right → no error."""
        yaml = _make_if_yaml(_VALID_UNARY_TRUE_CONDITION)
        errors = _fe001_errors(yaml)
        assert not any('If condition' in e for e in errors)

    def test_valid_unary_false(self):
        """Unary operator False (12) without right → no error."""
        yaml = _make_if_yaml(_VALID_UNARY_FALSE_CONDITION)
        errors = _fe001_errors(yaml)
        assert not any('If condition' in e for e in errors)

    def test_binary_with_literal_right(self):
        """Binary condition with literal right value → no error."""
        yaml = _make_if_yaml(_VALID_BINARY_CONDITION)
        errors = _fe001_errors(yaml)
        assert not any('right operand' in e for e in errors)


# ── Negative tests ──────────────────────────────────────────────

class TestIF001_Negative:
    """Invalid if-node conditions → FE-001 errors."""

    def test_missing_left(self):
        """Missing left operand → error."""
        yaml = _make_if_yaml(_MISSING_LEFT_CONDITION)
        errors = _fe001_errors(yaml)
        assert any('left operand is required' in e for e in errors)

    def test_missing_operator(self):
        """Missing operator → error."""
        yaml = _make_if_yaml(_MISSING_OPERATOR_CONDITION)
        errors = _fe001_errors(yaml)
        assert any('operator is required' in e for e in errors)

    def test_missing_right_binary(self):
        """Binary operator without right → error."""
        yaml = _make_if_yaml(_MISSING_RIGHT_BINARY_CONDITION)
        errors = _fe001_errors(yaml)
        assert any('right operand is required' in e for e in errors)

    def test_missing_right_unary_no_error(self):
        """Unary operator without right → no error (right not required)."""
        yaml = _make_if_yaml(_VALID_UNARY_NULL_CONDITION)
        errors = _fe001_errors(yaml)
        assert not any('right operand' in e for e in errors)


# ── Edge cases ──────────────────────────────────────────────────

class TestIF001_EdgeCases:
    """Edge cases for if-node condition validation."""

    def test_empty_conditions_list(self):
        """Empty conditions list → no condition errors."""
        yaml = _make_if_yaml('')
        errors = _fe001_errors(yaml)
        assert not any('If condition' in e for e in errors)

    def test_multiple_conditions(self):
        """Multiple conditions: one valid, one missing left → error for missing left."""
        multi = _VALID_BINARY_CONDITION + _MISSING_LEFT_CONDITION
        yaml = _make_if_yaml(multi)
        errors = _fe001_errors(yaml)
        assert any('left operand is required' in e for e in errors)

    def test_two_valid_binary_conditions(self):
        """Two valid binary conditions → no errors."""
        multi = _VALID_BINARY_CONDITION + _VALID_BINARY_CONDITION
        yaml = _make_if_yaml(multi)
        errors = _fe001_errors(yaml)
        assert not any('If condition' in e for e in errors)

    def test_mixed_unary_and_binary(self):
        """Mix of unary (Null) and binary conditions → no errors."""
        multi = _VALID_UNARY_NULL_CONDITION + _VALID_BINARY_CONDITION
        yaml = _make_if_yaml(multi)
        errors = _fe001_errors(yaml)
        assert not any('If condition' in e for e in errors)
