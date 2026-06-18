"""FE-001: Input 节点 (type 30) 字段验证。

规则来源: form-meta-rules.json FORM-input-001..002

验证规则:
  - nodeMeta 标题验证 (FORM-input-001)
  - outputs — 输出变量验证 (名称唯一性) (FORM-input-002)

NOTE: 输出唯一性由 FE-013 (SPEC-OUT-006) 统一处理。
"""
from __future__ import annotations

from tests.conftest import compile_text


def _fe001_errors(yaml_text: str) -> list[str]:
    """Extract SEMANTIC-FE-001 diagnostics."""
    report = compile_text(yaml_text)
    return [d.message for d in report.diagnostics if d.rule_id == 'SEMANTIC-FE-001']


def _fe013_errors(yaml_text: str) -> list[str]:
    """Extract SEMANTIC-FE-013 diagnostics."""
    report = compile_text(yaml_text)
    return [d.message for d in report.diagnostics if d.rule_id == 'SEMANTIC-FE-013']


def _make_input_yaml(
    title: str = 'Input',
    outputs: str | None = None,
) -> str:
    """Build a minimal workflow with an input node (type 30)."""
    outputs_section = ''
    if outputs is not None:
        outputs_section = f'\n      outputs:\n{outputs}'

    return f"""
nodes:
  - id: '100001'
    type: '1'
    data:
      nodeMeta:
        title: Start
  - id: 'i1'
    type: '30'
    data:
      nodeMeta:
        title: '{title}'{outputs_section}
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

class TestFE001_Input_Positive:
    """Valid input node configurations → no FE-001 errors."""

    def test_input_no_outputs(self):
        """Input node without outputs → no FE-001 error."""
        yaml = _make_input_yaml()
        errors = _fe001_errors(yaml)
        assert not errors

    def test_input_with_valid_output(self):
        """Input node with valid output → no FE-001/013 error."""
        yaml = _make_input_yaml(outputs=(
            "        - name: 'userInput'\n"
            "          type: 'string'"
        ))
        fe001 = _fe001_errors(yaml)
        fe013 = _fe013_errors(yaml)
        assert not fe001
        assert not fe013

    def test_input_with_multiple_outputs(self):
        """Input node with multiple valid outputs → no errors."""
        yaml = _make_input_yaml(outputs=(
            "        - name: 'query'\n"
            "          type: 'string'\n"
            "        - name: 'limit'\n"
            "          type: 'integer'"
        ))
        fe001 = _fe001_errors(yaml)
        fe013 = _fe013_errors(yaml)
        assert not fe001
        assert not fe013


# ── Negative ─────────────────────────────────────────────────────

class TestFE001_Input_Negative:
    """Invalid input node configurations → errors."""

    def test_input_output_reserved_word(self):
        """Input output with reserved word → FE-013 error."""
        yaml = _make_input_yaml(outputs=(
            "        - name: 'null'\n"
            "          type: 'string'"
        ))
        fe013 = _fe013_errors(yaml)
        assert any('reserved' in e.lower() for e in fe013)

    def test_input_output_invalid_format(self):
        """Input output with invalid format → FE-013 error."""
        yaml = _make_input_yaml(outputs=(
            "        - name: 'bad-name'\n"
            "          type: 'string'"
        ))
        fe013 = _fe013_errors(yaml)
        assert any('invalid format' in e.lower() for e in fe013)
