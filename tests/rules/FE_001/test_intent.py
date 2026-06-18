"""FE-001: Intent 节点 (type 22) 字段验证。

验证规则:
  - 至少需要一个输入参数 (第一个输入必填)

Tests cover:
  - Valid intent with input
  - Missing input (empty inputParameters)
  - Multiple inputs (one valid is enough)
  - Input with ref value
  - Input with literal value
"""

from tests.conftest import compile_text


def _fe001_errors(yaml_text: str) -> list[str]:
    report = compile_text(yaml_text)
    return [
        d.message for d in report.diagnostics
        if d.rule_id == 'SEMANTIC-FE-001'
    ]


def _make_intent_yaml(input_params: str | None = None) -> str:
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
  - id: 'i1'
    type: '22'
    data:
      nodeMeta:
        title: Intent
      inputs:{input_block}
  - id: '900001'
    type: '2'
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: '100001'
    targetNodeID: 'i1'
  - sourceNodeID: 'i1'
    targetNodeID: '900001'
"""


# ── Positive ─────────────────────────────────────────────────────

class TestFE001_Intent_Positive:
    """Valid intent configurations → no FE-001 errors."""

    def test_with_ref_input(self):
        """Intent with ref input → valid."""
        params = """          - name: query
            input:
              type: string
              value:
                type: ref
                content:
                  source: block-output
                  blockId: '100001'
                  name: output"""
        yaml = _make_intent_yaml(params)
        errors = _fe001_errors(yaml)
        assert not any('intent' in e.lower() for e in errors)

    def test_with_literal_input(self):
        """Intent with literal input → valid."""
        params = """          - name: query
            input:
              type: string
              value:
                type: literal
                content: 'test query'"""
        yaml = _make_intent_yaml(params)
        errors = _fe001_errors(yaml)
        assert not any('intent' in e.lower() for e in errors)

    def test_with_multiple_inputs(self):
        """Intent with multiple inputs → valid."""
        params = """          - name: query
            input:
              type: string
              value:
                type: literal
                content: 'test'
          - name: context
            input:
              type: string
              value:
                type: literal
                content: 'ctx'"""
        yaml = _make_intent_yaml(params)
        errors = _fe001_errors(yaml)
        assert not any('intent' in e.lower() for e in errors)


# ── Negative ─────────────────────────────────────────────────────

class TestFE001_Intent_Negative:
    """Invalid intent configurations → FE-001 errors."""

    def test_no_inputs(self):
        """Empty inputParameters → error."""
        yaml = _make_intent_yaml(input_params=None)
        errors = _fe001_errors(yaml)
        assert any('intent' in e.lower() for e in errors)


# ── Edge cases ──────────────────────────────────────────────────

class TestFE001_Intent_EdgeCases:
    """Edge cases for intent node validation."""

    def test_input_with_empty_name(self):
        """Input with empty name → still has input, so no 'intent' error."""
        params = """          - name: ''
            input:
              type: string
              value:
                type: literal
                content: 'test'"""
        yaml = _make_intent_yaml(params)
        errors = _fe001_errors(yaml)
        # Input exists, so no "intent" missing input error
        assert not any('intent' in e.lower() for e in errors)
