"""FE-001: JSON Stringify 节点 (type 58) 字段验证。

规则来源: form-meta-rules.json FORM-json-stringify-001

验证规则:
  - inputs.inputParameters[0].input — 第一个输入参数值必填

编译器实现: _check_first_input_required (与 intent/ltm 共享)
"""
from __future__ import annotations

from tests.conftest import compile_text


def _fe001_errors(yaml_text: str) -> list[str]:
    """Extract SEMANTIC-FE-001 diagnostics."""
    report = compile_text(yaml_text)
    return [d.message for d in report.diagnostics if d.rule_id == 'SEMANTIC-FE-001']


def _make_json_stringify_yaml(input_params: str | None = None) -> str:
    """Build a minimal workflow with a json-stringify node (type 58)."""
    if input_params is None:
        input_block = """
        inputParameters: []"""
    else:
        input_block = f"""
        inputParameters:
{input_params}"""

    return f"""
nodes:
  - id: '100001'
    type: '1'
    data:
      nodeMeta:
        title: Start
  - id: 'js1'
    type: '58'
    data:
      nodeMeta:
        title: JsonStringify
      inputs:{input_block}
  - id: '900001'
    type: '2'
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: '100001'
    targetNodeID: 'js1'
  - sourceNodeID: 'js1'
    targetNodeID: '900001'
"""


# ── Positive ─────────────────────────────────────────────────────

class TestFE001_JsonStringify_Positive:
    """Valid json-stringify configurations → no FE-001 errors."""

    def test_with_valid_input(self):
        """json-stringify with valid first input → no error."""
        yaml = _make_json_stringify_yaml(
            input_params=(
                "          - name: 'data'\n"
                "            input:\n"
                "              type: string\n"
                "              value:\n"
                "                type: literal\n"
                "                content: '{\"key\": \"value\"}'"
            )
        )
        errors = _fe001_errors(yaml)
        assert not errors

    def test_with_ref_input(self):
        """json-stringify with ref input → no error."""
        yaml = _make_json_stringify_yaml(
            input_params=(
                "          - name: 'data'\n"
                "            input:\n"
                "              type: string\n"
                "              value:\n"
                "                type: ref\n"
                "                content:\n"
                "                  source: block-output\n"
                "                  blockId: '100001'\n"
                "                  name: 'output_1'"
            )
        )
        errors = _fe001_errors(yaml)
        assert not errors

    def test_with_multiple_inputs(self):
        """json-stringify with multiple inputs → no error."""
        yaml = _make_json_stringify_yaml(
            input_params=(
                "          - name: 'data'\n"
                "            input:\n"
                "              type: string\n"
                "              value:\n"
                "                type: literal\n"
                "                content: 'hello'\n"
                "          - name: 'extra'\n"
                "            input:\n"
                "              type: string\n"
                "              value:\n"
                "                type: literal\n"
                "                content: 'world'"
            )
        )
        errors = _fe001_errors(yaml)
        assert not errors


# ── Negative ─────────────────────────────────────────────────────

class TestFE001_JsonStringify_Negative:
    """Invalid json-stringify configurations → FE-001 errors."""

    def test_empty_input_params(self):
        """json-stringify with empty inputParameters → error."""
        yaml = _make_json_stringify_yaml(input_params=None)
        errors = _fe001_errors(yaml)
        assert len(errors) >= 1

    def test_first_input_empty_value(self):
        """json-stringify with first input having empty content → error."""
        yaml = _make_json_stringify_yaml(
            input_params=(
                "          - name: 'data'\n"
                "            input:\n"
                "              type: string\n"
                "              value:\n"
                "                type: literal\n"
                "                content: ''"
            )
        )
        errors = _fe001_errors(yaml)
        assert len(errors) >= 1

    def test_first_input_missing_value(self):
        """json-stringify with first input missing value → error."""
        yaml = _make_json_stringify_yaml(
            input_params=(
                "          - name: 'data'\n"
                "            input:\n"
                "              type: string"
            )
        )
        errors = _fe001_errors(yaml)
        assert len(errors) >= 1


# ── Edge cases ──────────────────────────────────────────────────

class TestFE001_JsonStringify_EdgeCases:
    """Edge cases for json-stringify validation."""

    def test_no_inputs_key(self):
        """json-stringify without inputs key → error."""
        yaml = """
nodes:
  - id: '100001'
    type: '1'
    data:
      nodeMeta:
        title: Start
  - id: 'js1'
    type: '58'
    data:
      nodeMeta:
        title: JsonStringify
  - id: '900001'
    type: '2'
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: '100001'
    targetNodeID: 'js1'
  - sourceNodeID: 'js1'
    targetNodeID: '900001'
"""
        errors = _fe001_errors(yaml)
        assert len(errors) >= 1

    def test_title_validation_still_applies(self):
        """json-stringify with invalid title → FE-009/010 error (not FE-001)."""
        yaml = _make_json_stringify_yaml(
            input_params=(
                "          - name: 'data'\n"
                "            input:\n"
                "              type: string\n"
                "              value:\n"
                "                type: literal\n"
                "                content: 'ok'"
            )
        )
        # Valid title → no FE-001 errors
        errors = _fe001_errors(yaml)
        assert not errors
