"""FE-001: LTM 节点 (type 26) 字段验证。

验证规则:
  - 至少需要一个输入参数 (第一个输入必填)

Tests cover:
  - Valid LTM with input
  - Missing input (empty inputParameters)
  - LTM with multiple inputs
  - LTM with ref input value
  - LTM with literal input value
"""

from tests.conftest import compile_text


def _fe001_errors(yaml_text: str) -> list[str]:
    report = compile_text(yaml_text)
    return [
        d.message for d in report.diagnostics
        if d.rule_id == 'SEMANTIC-FE-001'
    ]


def _make_ltm_yaml(input_params: str | None = None) -> str:
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
  - id: 'ltm1'
    type: '26'
    data:
      nodeMeta:
        title: LTM
      inputs:{input_block}
  - id: '900001'
    type: '2'
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: '100001'
    targetNodeID: 'ltm1'
  - sourceNodeID: 'ltm1'
    targetNodeID: '900001'
"""


# ── Positive ─────────────────────────────────────────────────────

class TestFE001_LTM_Positive:
    """Valid LTM configurations → no FE-001 errors."""

    def test_with_literal_input(self):
        """LTM with literal input → valid."""
        params = """          - name: query
            input:
              type: string
              value:
                type: literal
                content: 'test query'"""
        yaml = _make_ltm_yaml(params)
        errors = _fe001_errors(yaml)
        assert not any('ltm' in e.lower() for e in errors)

    def test_with_ref_input(self):
        """LTM with ref input → valid."""
        params = """          - name: query
            input:
              type: string
              value:
                type: ref
                content:
                  source: block-output
                  blockId: '100001'
                  name: output"""
        yaml = _make_ltm_yaml(params)
        errors = _fe001_errors(yaml)
        assert not any('ltm' in e.lower() for e in errors)

    def test_with_multiple_inputs(self):
        """LTM with multiple inputs → valid."""
        params = """          - name: query
            input:
              type: string
              value:
                type: literal
                content: 'search'
          - name: user_id
            input:
              type: string
              value:
                type: literal
                content: 'u1'"""
        yaml = _make_ltm_yaml(params)
        errors = _fe001_errors(yaml)
        assert not any('ltm' in e.lower() for e in errors)


# ── Negative ─────────────────────────────────────────────────────

class TestFE001_LTM_Negative:
    """Invalid LTM configurations → FE-001 errors."""

    def test_no_inputs(self):
        """Empty inputParameters → error."""
        yaml = _make_ltm_yaml(input_params=None)
        errors = _fe001_errors(yaml)
        assert any('ltm' in e.lower() for e in errors)


# ── Edge cases ──────────────────────────────────────────────────

class TestFE001_LTM_EdgeCases:
    """Edge cases for LTM node validation."""

    def test_input_with_empty_name(self):
        """Input with empty name → still has input, so no LTM error."""
        params = """          - name: ''
            input:
              type: string
              value:
                type: literal
                content: 'test'"""
        yaml = _make_ltm_yaml(params)
        errors = _fe001_errors(yaml)
        assert not any('ltm' in e.lower() for e in errors)

    def test_no_inputs_key_at_all(self):
        """No inputs key at all → error."""
        yaml = """
nodes:
  - id: '100001'
    type: '1'
    data:
      nodeMeta:
        title: Start
  - id: 'ltm1'
    type: '26'
    data:
      nodeMeta:
        title: LTM
  - id: '900001'
    type: '2'
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: '100001'
    targetNodeID: 'ltm1'
  - sourceNodeID: 'ltm1'
    targetNodeID: '900001'
"""
        errors = _fe001_errors(yaml)
        assert any('ltm' in e.lower() for e in errors)
