"""FE-001: Start 节点 (type 1) 字段验证。

规则来源: form-meta-rules.json FORM-start-001..004

验证规则:
  - nodeMeta 标题验证 (FORM-start-001)
  - outputs — 输出变量验证 (名称唯一性) (FORM-start-002)
  - trigger.dynamicInputs.* — 触发器动态输入 (FORM-start-003, custom_inline)
  - trigger.parameters.* — 触发器参数 (FORM-start-004, custom_inline)

NOTE: FORM-start-003/004 为 custom_inline，依赖触发器配置，暂不测试。
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


def _make_start_yaml(
    title: str = 'Start',
    outputs: str | None = None,
) -> str:
    """Build a minimal workflow with a customized start node."""
    outputs_section = ''
    if outputs is not None:
        outputs_section = f'\n      outputs:\n{outputs}'

    return f"""
nodes:
  - id: '100001'
    type: '1'
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
    targetNodeID: '900001'
"""


# ── Positive ─────────────────────────────────────────────────────

class TestFE001_Start_Positive:
    """Valid start node configurations → no FE-001 errors."""

    def test_start_no_outputs(self):
        """Start node without outputs → no FE-001 error."""
        yaml = _make_start_yaml()
        errors = _fe001_errors(yaml)
        assert not errors

    def test_start_with_valid_output(self):
        """Start node with valid output variable → no FE-001/013 error."""
        yaml = _make_start_yaml(outputs=(
            "        - name: 'input_1'\n"
            "          type: 'string'"
        ))
        fe001 = _fe001_errors(yaml)
        fe013 = _fe013_errors(yaml)
        assert not fe001
        assert not fe013

    def test_start_with_multiple_outputs(self):
        """Start node with multiple valid outputs → no errors."""
        yaml = _make_start_yaml(outputs=(
            "        - name: 'userInput'\n"
            "          type: 'string'\n"
            "        - name: 'config'\n"
            "          type: 'object'"
        ))
        fe001 = _fe001_errors(yaml)
        fe013 = _fe013_errors(yaml)
        assert not fe001
        assert not fe013


# ── Negative ─────────────────────────────────────────────────────

class TestFE001_Start_Negative:
    """Invalid start node configurations → errors."""

    def test_start_output_reserved_word(self):
        """Start output with reserved word → FE-013 error."""
        yaml = _make_start_yaml(outputs=(
            "        - name: 'true'\n"
            "          type: 'boolean'"
        ))
        fe013 = _fe013_errors(yaml)
        assert any('reserved' in e.lower() for e in fe013)

    def test_start_output_empty_name(self):
        """Start output with empty name → FE-013 error."""
        yaml = _make_start_yaml(outputs=(
            "        - name: ''\n"
            "          type: 'string'"
        ))
        fe013 = _fe013_errors(yaml)
        assert fe013

    def test_start_output_invalid_format(self):
        """Start output with digit-start name → FE-013 error."""
        yaml = _make_start_yaml(outputs=(
            "        - name: '1input'\n"
            "          type: 'string'"
        ))
        fe013 = _fe013_errors(yaml)
        assert any('invalid format' in e.lower() for e in fe013)
