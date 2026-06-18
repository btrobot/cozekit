"""FE-001: Variable 节点 (type 11) 字段验证。

规则来源: form-meta-rules.json FORM-variable-001..002

验证规则:
  - inputParameters.*.name — 变量名称非空验证 (FORM-variable-001)
  - inputParameters.*.input — 变量输入参数值必填验证 (FORM-variable-002)

NOTE: 编译器当前无 _check_variable_node_fields 处理器。
"""
from __future__ import annotations

import pytest

from tests.conftest import compile_text


def _fe001_errors(yaml_text: str) -> list[str]:
    """Extract SEMANTIC-FE-001 diagnostics."""
    report = compile_text(yaml_text)
    return [d.message for d in report.diagnostics if d.rule_id in ('SEMANTIC-FE-001', 'SEMANTIC-FE-014')]


def _make_variable_yaml(
    title: str = 'VarNode',
    params: str = '          []',
) -> str:
    """Build a minimal workflow with a variable node (type 11)."""
    return f"""
nodes:
  - id: '100001'
    type: '1'
    data:
      nodeMeta:
        title: Start
  - id: 'v1'
    type: '11'
    data:
      nodeMeta:
        title: '{title}'
      inputs:
        inputParameters:
{params}
  - id: '900001'
    type: '2'
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: '100001'
    targetNodeID: 'v1'
  - sourceNodeID: 'v1'
    targetNodeID: '900001'
"""


# ── Positive ─────────────────────────────────────────────────────

class TestFE001_Variable_Positive:
    """Valid variable node configurations → no FE-001 errors."""

    def test_valid_empty_params(self):
        """Variable node with empty params → no FE-001 error."""
        yaml = _make_variable_yaml()
        errors = _fe001_errors(yaml)
        assert not errors

    def test_valid_with_param(self):
        """Variable node with valid parameter → no FE-001 error."""
        yaml = _make_variable_yaml(params=(
            "          - name: 'myVar'\n"
            "            input:\n"
            "              type: 'string'\n"
            "              value:\n"
            "                type: 'literal'\n"
            "                content: 'hello'"
        ))
        errors = _fe001_errors(yaml)
        assert not errors

    def test_valid_with_ref_value(self):
        """Variable node with ref value → no FE-001 error."""
        yaml = _make_variable_yaml(params=(
            "          - name: 'counter'\n"
            "            input:\n"
            "              type: 'integer'\n"
            "              value:\n"
            "                type: 'ref'\n"
            "                content:\n"
            "                  source: 'global_variable_app'\n"
            "                  name: 'myCounter'"
        ))
        errors = _fe001_errors(yaml)
        assert not errors


# ── Negative ─────────────────────────────────────────────────────

class TestFE001_Variable_Negative:
    """Invalid variable node configurations → FE-001 errors (when implemented)."""
    def test_variable_empty_name(self):
        """Variable parameter with empty name → should error."""
        yaml = _make_variable_yaml(params=(
            "          - name: ''\n"
            "            input:\n"
            "              type: 'string'\n"
            "              value:\n"
            "                type: 'literal'\n"
            "                content: 'hello'"
        ))
        errors = _fe001_errors(yaml)
        assert any('name' in e.lower() for e in errors)
    def test_variable_missing_input_value(self):
        """Variable parameter with missing input value → should error."""
        yaml = _make_variable_yaml(params=(
            "          - name: 'myVar'\n"
            "            input:\n"
            "              type: 'string'"
        ))
        errors = _fe001_errors(yaml)
        assert any('value' in e.lower() or 'input' in e.lower() for e in errors)
