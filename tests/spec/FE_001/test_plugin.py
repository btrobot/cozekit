"""FE-001: Plugin 节点 (type 4) 静态验证。

验证规则:
  - inputParameters 值表达式格式合法 (type + content)
  - 不检查是否 required (依赖 API 定义，运行时)
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


_PLUGIN_YAML_TEMPLATE = """\
nodes:
  - id: '100001'
    type: '1'
    data:
      nodeMeta:
        title: Start
  - id: 'plugin-1'
    type: '4'
    data:
      nodeMeta:
        title: Plugin
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
    targetNodeID: 'plugin-1'
  - sourceNodeID: 'plugin-1'
    targetNodeID: '900001'
"""


def _make_plugin_yaml(input_params_yaml: str) -> str:
    return _PLUGIN_YAML_TEMPLATE.format(input_params=input_params_yaml)


# ── Positive tests ──────────────────────────────────────────────

class TestPlugin_Positive:
    """Valid plugin node configurations."""

    def test_valid_ref_input(self):
        """Valid ref type input → no error."""
        yaml = _make_plugin_yaml(
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
        assert not any('Plugin node' in e for e in errors)

    def test_valid_literal_input(self):
        """Valid literal type input → no error."""
        yaml = _make_plugin_yaml(
            "          - name: param1\n"
            "            input:\n"
            "              type: string\n"
            "              value:\n"
            "                type: literal\n"
            "                content: 'hello'"
        )
        errors = _fe001_errors(yaml)
        assert not any('Plugin node' in e for e in errors)

    def test_empty_input_parameters(self):
        """Empty inputParameters → no error (not required)."""
        yaml = _make_plugin_yaml("")
        errors = _fe001_errors(yaml)
        assert not any('Plugin node' in e for e in errors)


# ── Negative tests ──────────────────────────────────────────────

class TestPlugin_Negative:
    """Invalid plugin node configurations."""

    def test_invalid_value_type(self):
        """Invalid value type → error."""
        yaml = _make_plugin_yaml(
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

class TestPlugin_EdgeCases:
    """Edge cases for plugin node validation."""

    def test_multiple_inputs(self):
        """Multiple inputs - one invalid, one valid."""
        yaml = _make_plugin_yaml(
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
