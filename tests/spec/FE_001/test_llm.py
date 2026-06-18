"""FE-001: LLM 节点 (type 3) 字段验证。

规则定义: docs/rule-impl/FE-001-validateNode.md
实现代码: passes/semantic_pass.py::SemanticPass._check_llm_fields
AST提取: ast/builder.py::_extract_node_specific_params_raw (LLM_NODE_TYPE_ID)

验证规则:
  - modelType 必填 (必须选择模型)
  - temperature 范围 [0, 2]
  - maxTokens > 0
"""

import pytest

from tests.conftest import compile_text


# ── Helpers ──────────────────────────────────────────────────────

def _llm_errors(yaml_text: str) -> list[str]:
    """Extract FE-001 diagnostics mentioning LLM fields."""
    report = compile_text(yaml_text)
    return [
        d.message for d in report.diagnostics
        if d.rule_id == 'SEMANTIC-FE-001'
    ]


def _make_llm_yaml(
    model_type: str | None = '1001',
    temperature: str | None = None,
    max_tokens: str | None = None,
    prompt: str | None = 'Hello',
) -> str:
    """Build a minimal workflow with an LLM node."""
    params = []
    if model_type is not None:
        params.append(
            f"          - name: modelType\n"
            f"            input:\n"
            f"              type: integer\n"
            f"              value:\n"
            f"                type: literal\n"
            f"                content: '{model_type}'"
        )
    if temperature is not None:
        params.append(
            f"          - name: temperature\n"
            f"            input:\n"
            f"              type: float\n"
            f"              value:\n"
            f"                type: literal\n"
            f"                content: '{temperature}'"
        )
    if max_tokens is not None:
        params.append(
            f"          - name: maxTokens\n"
            f"            input:\n"
            f"              type: integer\n"
            f"              value:\n"
            f"                type: literal\n"
            f"                content: '{max_tokens}'"
        )
    if prompt is not None:
        params.append(
            f"          - name: prompt\n"
            f"            input:\n"
            f"              type: string\n"
            f"              value:\n"
            f"                type: literal\n"
            f"                content: '{prompt}'"
        )

    params_block = '\n'.join(params) if params else '          []'

    return f"""
nodes:
  - id: '100001'
    type: '1'
    data:
      nodeMeta:
        title: Start
  - id: 'llm-1'
    type: '3'
    data:
      nodeMeta:
        title: LLM
      inputs:
        inputParameters: []
        llmParam:
{params_block}
  - id: '900001'
    type: '2'
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: '100001'
    targetNodeID: 'llm-1'
  - sourceNodeID: 'llm-1'
    targetNodeID: '900001'
"""


# ── Positive tests ───────────────────────────────────────────────

class TestFE001_LLM_Positive:
    """合法 LLM 节点不触发 FE-001。"""

    def test_with_model_type_ok(self):
        yaml = _make_llm_yaml(model_type='1001')
        errors = _llm_errors(yaml)
        assert not any('modelType' in e for e in errors)

    def test_temperature_in_range(self):
        yaml = _make_llm_yaml(model_type='1001', temperature='0.8')
        errors = _llm_errors(yaml)
        assert not any('temperature' in e for e in errors)

    def test_temperature_at_min(self):
        yaml = _make_llm_yaml(model_type='1001', temperature='0')
        errors = _llm_errors(yaml)
        assert not any('temperature' in e for e in errors)

    def test_temperature_at_max(self):
        yaml = _make_llm_yaml(model_type='1001', temperature='2')
        errors = _llm_errors(yaml)
        assert not any('temperature' in e for e in errors)

    def test_max_tokens_positive(self):
        yaml = _make_llm_yaml(model_type='1001', max_tokens='512')
        errors = _llm_errors(yaml)
        assert not any('maxTokens' in e for e in errors)


# ── Negative tests ───────────────────────────────────────────────

class TestFE001_LLM_Negative:
    """非法 LLM 节点必须触发 FE-001。"""

    def test_missing_model_type(self):
        yaml = _make_llm_yaml(model_type=None)
        errors = _llm_errors(yaml)
        assert any('modelType' in e for e in errors)

    def test_temperature_below_range(self):
        yaml = _make_llm_yaml(model_type='1001', temperature='-0.1')
        errors = _llm_errors(yaml)
        assert any('temperature' in e for e in errors)

    def test_temperature_above_range(self):
        yaml = _make_llm_yaml(model_type='1001', temperature='3.0')
        errors = _llm_errors(yaml)
        assert any('temperature' in e for e in errors)

    def test_max_tokens_zero(self):
        yaml = _make_llm_yaml(model_type='1001', max_tokens='0')
        errors = _llm_errors(yaml)
        assert any('maxTokens' in e for e in errors)

    def test_max_tokens_negative(self):
        yaml = _make_llm_yaml(model_type='1001', max_tokens='-1')
        errors = _llm_errors(yaml)
        assert any('maxTokens' in e for e in errors)


# ── Edge cases ───────────────────────────────────────────────────

class TestFE001_LLM_EdgeCases:
    """边界条件。"""

    def test_llm_node_with_no_params_at_all(self):
        """LLM node without llmParam section — should still flag modelType missing."""
        yaml = """
nodes:
  - id: '100001'
    type: '1'
    data:
      nodeMeta:
        title: Start
  - id: 'llm-1'
    type: '3'
    data:
      nodeMeta:
        title: LLM
      inputs:
        inputParameters: []
  - id: '900001'
    type: '2'
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: '100001'
    targetNodeID: 'llm-1'
  - sourceNodeID: 'llm-1'
    targetNodeID: '900001'
"""
        errors = _llm_errors(yaml)
        assert any('modelType' in e for e in errors)

    def test_temperature_ref_not_checked(self):
        """Temperature as a ref (not literal) — range check skipped."""
        yaml = """
nodes:
  - id: '100001'
    type: '1'
    data:
      nodeMeta:
        title: Start
  - id: 'llm-1'
    type: '3'
    data:
      nodeMeta:
        title: LLM
      inputs:
        inputParameters: []
        llmParam:
          - name: modelType
            input:
              type: integer
              value:
                type: literal
                content: '1001'
          - name: temperature
            input:
              type: float
              value:
                type: ref
                content:
                  source: block-output
                  blockId: '100001'
                  name: temp
  - id: '900001'
    type: '2'
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: '100001'
    targetNodeID: 'llm-1'
  - sourceNodeID: 'llm-1'
    targetNodeID: '900001'
"""
        errors = _llm_errors(yaml)
        assert not any('temperature' in e for e in errors)


# ── Prompt / systemPrompt tests ──────────────────────────────────

class TestFE001_LLM_PromptSystemPrompt:
    """Prompt and systemPrompt validation.

    In coze-studio, prompt is only required when model.is_up_required is true.
    Since we can't determine this at compile time, we accept systemPrompt-only.
    """

    def test_system_prompt_only_ok(self):
        """LLM with systemPrompt but empty prompt → no error."""
        yaml = _make_llm_yaml(prompt='', )  # no prompt, add systemPrompt below
        # Add systemPrompt via manual YAML
        yaml = """
nodes:
  - id: '100001'
    type: '1'
    data:
      nodeMeta:
        title: Start
  - id: 'llm-1'
    type: '3'
    data:
      nodeMeta:
        title: LLM
      inputs:
        inputParameters: []
        llmParam:
          - name: modelType
            input:
              type: integer
              value:
                type: literal
                content: '1001'
          - name: prompt
            input:
              type: string
              value:
                type: literal
                content: ''
          - name: systemPrompt
            input:
              type: string
              value:
                type: literal
                content: 'You are a helpful assistant'
  - id: '900001'
    type: '2'
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: '100001'
    targetNodeID: 'llm-1'
  - sourceNodeID: 'llm-1'
    targetNodeID: '900001'
"""
        errors = _llm_errors(yaml)
        assert not any('prompt' in e.lower() for e in errors)

    def test_both_empty_flagged(self):
        """LLM with both prompt and systemPrompt empty → error."""
        yaml = """
nodes:
  - id: '100001'
    type: '1'
    data:
      nodeMeta:
        title: Start
  - id: 'llm-1'
    type: '3'
    data:
      nodeMeta:
        title: LLM
      inputs:
        inputParameters: []
        llmParam:
          - name: modelType
            input:
              type: integer
              value:
                type: literal
                content: '1001'
          - name: prompt
            input:
              type: string
              value:
                type: literal
                content: ''
          - name: systemPrompt
            input:
              type: string
              value:
                type: literal
                content: ''
  - id: '900001'
    type: '2'
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: '100001'
    targetNodeID: 'llm-1'
  - sourceNodeID: 'llm-1'
    targetNodeID: '900001'
"""
        errors = _llm_errors(yaml)
        assert any('prompt' in e.lower() for e in errors)

    def test_prompt_only_ok(self):
        """LLM with prompt but no systemPrompt → no error."""
        yaml = _make_llm_yaml(prompt='Hello world')
        errors = _llm_errors(yaml)
        assert not any('prompt' in e.lower() for e in errors)
