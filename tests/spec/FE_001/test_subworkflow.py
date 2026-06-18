"""FE-001: SubWorkflow 节点 (type 9) 静态验证。

验证规则:
  - inputParameters 值表达式格式合法 (type + content)
  - 不检查是否 required (依赖子工作流定义，运行时)
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


_SUBWORKFLOW_YAML_TEMPLATE = """\
nodes:
  - id: '100001'
    type: '1'
    data:
      nodeMeta:
        title: Start
  - id: 'subwf-1'
    type: '9'
    data:
      nodeMeta:
        title: SubWorkflow
      inputs:
        inputParameters:
{input_params}
  - id: '900001'
    type: '2'
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: '100001'
    targetNodeID: 'subwf-1'
  - sourceNodeID: 'subwf-1'
    targetNodeID: '900001'
"""


def _make_subworkflow_yaml(input_params_yaml: str) -> str:
    return _SUBWORKFLOW_YAML_TEMPLATE.format(input_params=input_params_yaml)


# ── Positive tests ──────────────────────────────────────────────

class TestSubWorkflow_Positive:
    """Valid subworkflow node configurations."""

    def test_valid_ref_input(self):
        """Valid ref type input → no error."""
        yaml = _make_subworkflow_yaml(
            "          - name: param1\n"
            "            input:\n"
            "              type: string\n"
            "              value:\n"
            "                type: ref\n"
            "                content:\n"
            "                  source: block-output\n"
            "                  blockID: '100001'\n"
            "                  name: 'input_1'"
        )
        errors = _fe001_errors(yaml)
        assert not any('SubWorkflow node' in e for e in errors)

    def test_valid_literal_input(self):
        """Valid literal type input → no error."""
        yaml = _make_subworkflow_yaml(
            "          - name: param1\n"
            "            input:\n"
            "              type: string\n"
            "              value:\n"
            "                type: literal\n"
            "                content: 'hello'"
        )
        errors = _fe001_errors(yaml)
        assert not any('SubWorkflow node' in e for e in errors)

    def test_empty_input_parameters(self):
        """Empty inputParameters → no error (not required)."""
        yaml = _make_subworkflow_yaml("")
        errors = _fe001_errors(yaml)
        assert not any('SubWorkflow node' in e for e in errors)


# ── Negative tests ──────────────────────────────────────────────

class TestSubWorkflow_Negative:
    """Invalid subworkflow node configurations."""

    def test_invalid_value_type(self):
        """Invalid value type → error."""
        yaml = _make_subworkflow_yaml(
            "          - name: param1\n"
            "            input:\n"
            "              type: string\n"
            "              value:\n"
            "                type: invalid_type\n"
            "                content: 'hello'"
        )
        errors = _fe001_errors(yaml)
        assert any('invalid value type' in e for e in errors)


# ── Edge cases ──────────────────────────────────────────────────

class TestSubWorkflow_EdgeCases:
    """Edge cases for subworkflow node validation."""

    def test_multiple_inputs(self):
        """Multiple inputs - one invalid, one valid."""
        yaml = _make_subworkflow_yaml(
            "          - name: param1\n"
            "            input:\n"
            "              type: string\n"
            "              value:\n"
            "                type: ref\n"
            "                content:\n"
            "                  source: block-output\n"
            "                  blockID: '100001'\n"
            "                  name: 'input_1'\n"
            "          - name: param2\n"
            "            input:\n"
            "              type: string\n"
            "              value:\n"
            "                type: invalid\n"
            "                content: 'test'"
        )
        errors = _fe001_errors(yaml)
        assert any('invalid value type' in e for e in errors)
