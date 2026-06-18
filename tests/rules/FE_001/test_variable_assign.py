"""FE-001: Variable Assign 节点 (types 20/40) 字段验证。

验证规则:
  - left 必填 (目标变量)
  - right 必填 (赋值)

Tests cover:
  - Valid left and right
  - Both types (20, 40)
  - Empty params (both missing)
  - Missing left only
  - Missing right only
  - Type 40 empty params
  - Left as ref value
  - Right as literal value
  - Both as ref values
"""

import pytest

from tests.conftest import compile_text


def _fe001_errors(yaml_text: str) -> list[str]:
    report = compile_text(yaml_text)
    return [
        d.message for d in report.diagnostics
        if d.rule_id == 'SEMANTIC-FE-001'
    ]


def _make_var_assign_yaml(
    node_type: str = '20',
    left: str | None = 'myVar',
    right: str | None = 'hello',
) -> str:
    params = []
    if left is not None:
        params.append(
            f"          - name: left\n"
            f"            input:\n"
            f"              type: string\n"
            f"              value:\n"
            f"                type: ref\n"
            f"                content:\n"
            f"                  source: global_variable_app\n"
            f"                  name: '{left}'"
        )
    if right is not None:
        params.append(
            f"          - name: right\n"
            f"            input:\n"
            f"              type: string\n"
            f"              value:\n"
            f"                type: literal\n"
            f"                content: '{right}'"
        )

    params_block = '\n'.join(params) if params else '          []'

    return f"""
nodes:
  - id: '100001'
    type: '1'
    data:
      nodeMeta:
        title: Start
  - id: 'va1'
    type: '{node_type}'
    data:
      nodeMeta:
        title: SetVar
      inputs:
        inputParameters:
{params_block}
  - id: '900001'
    type: '2'
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: '100001'
    targetNodeID: 'va1'
  - sourceNodeID: 'va1'
    targetNodeID: '900001'
"""


# ── Positive ─────────────────────────────────────────────────────

class TestFE001_VariableAssign_Positive:
    """Valid variable assign configurations → no FE-001 errors."""

    def test_with_left_and_right(self):
        yaml = _make_var_assign_yaml()
        errors = _fe001_errors(yaml)
        assert not any('variable' in e.lower() for e in errors)

    @pytest.mark.parametrize("type_id", ['20', '40'])
    def test_both_types_ok(self, type_id):
        yaml = _make_var_assign_yaml(node_type=type_id)
        errors = _fe001_errors(yaml)
        assert not any('variable' in e.lower() for e in errors)

    def test_left_with_different_var_name(self):
        """Different variable name for left → valid."""
        yaml = _make_var_assign_yaml(left='counter')
        errors = _fe001_errors(yaml)
        assert not any('variable' in e.lower() for e in errors)

    def test_right_with_numeric_literal(self):
        """Right with numeric literal → valid."""
        yaml = _make_var_assign_yaml(right='42')
        errors = _fe001_errors(yaml)
        assert not any('variable' in e.lower() for e in errors)

    def test_right_with_empty_string(self):
        """Right with empty string literal → error (empty treated as missing)."""
        yaml = _make_var_assign_yaml(right='')
        errors = _fe001_errors(yaml)
        assert any('right' in e.lower() for e in errors)


# ── Negative ─────────────────────────────────────────────────────

class TestFE001_VariableAssign_Negative:
    """Invalid variable assign configurations → FE-001 errors."""

    def test_empty_params(self):
        """Both left and right missing → error."""
        yaml = _make_var_assign_yaml(left=None, right=None)
        errors = _fe001_errors(yaml)
        assert any('variable' in e.lower() for e in errors)

    def test_missing_left(self):
        """Missing left → error."""
        yaml = _make_var_assign_yaml(left=None)
        errors = _fe001_errors(yaml)
        assert any('left' in e.lower() for e in errors)

    def test_missing_right(self):
        """Missing right → error."""
        yaml = _make_var_assign_yaml(right=None)
        errors = _fe001_errors(yaml)
        assert any('right' in e.lower() for e in errors)

    def test_type_40_empty_params(self):
        """Type 40 with empty params → error."""
        yaml = _make_var_assign_yaml(node_type='40', left=None, right=None)
        errors = _fe001_errors(yaml)
        assert any('variable' in e.lower() for e in errors)

    @pytest.mark.parametrize("type_id", ['20', '40'])
    def test_missing_left_both_types(self, type_id):
        """Both types: missing left → error."""
        yaml = _make_var_assign_yaml(node_type=type_id, left=None)
        errors = _fe001_errors(yaml)
        assert any('left' in e.lower() for e in errors)

    @pytest.mark.parametrize("type_id", ['20', '40'])
    def test_missing_right_both_types(self, type_id):
        """Both types: missing right → error."""
        yaml = _make_var_assign_yaml(node_type=type_id, right=None)
        errors = _fe001_errors(yaml)
        assert any('right' in e.lower() for e in errors)


# ── Edge cases ──────────────────────────────────────────────────

class TestFE001_VariableAssign_EdgeCases:
    """Edge cases for variable assign node validation."""

    def test_both_as_ref_values(self):
        """Both left and right as ref values → valid."""
        yaml = """
nodes:
  - id: '100001'
    type: '1'
    data:
      nodeMeta:
        title: Start
  - id: 'va1'
    type: '20'
    data:
      nodeMeta:
        title: SetVar
      inputs:
        inputParameters:
          - name: left
            input:
              type: string
              value:
                type: ref
                content:
                  source: global_variable_app
                  name: 'targetVar'
          - name: right
            input:
              type: string
              value:
                type: ref
                content:
                  source: block-output
                  blockId: '100001'
                  name: 'input_1'
  - id: '900001'
    type: '2'
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: '100001'
    targetNodeID: 'va1'
  - sourceNodeID: 'va1'
    targetNodeID: '900001'
"""
        errors = _fe001_errors(yaml)
        assert not any('variable' in e.lower() for e in errors)
        assert not any('left' in e.lower() for e in errors)
        assert not any('right' in e.lower() for e in errors)

    def test_no_inputs_key_at_all(self):
        """No inputs key → error."""
        yaml = """
nodes:
  - id: '100001'
    type: '1'
    data:
      nodeMeta:
        title: Start
  - id: 'va1'
    type: '20'
    data:
      nodeMeta:
        title: SetVar
  - id: '900001'
    type: '2'
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: '100001'
    targetNodeID: 'va1'
  - sourceNodeID: 'va1'
    targetNodeID: '900001'
"""
        errors = _fe001_errors(yaml)
        assert any('variable' in e.lower() for e in errors)
