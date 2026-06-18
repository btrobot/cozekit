"""FE-001: Code 节点 (type 5) 字段验证。

验证规则:
  - code 内容必填 (codeParam.code 不能为空)

Tests cover:
  - Valid code content
  - Multiline code
  - Missing code param
  - Empty code string
  - Whitespace-only code
  - No code section at all
  - Code with special characters
"""

from tests.conftest import compile_text


def _fe001_errors(yaml_text: str) -> list[str]:
    report = compile_text(yaml_text)
    return [
        d.message for d in report.diagnostics
        if d.rule_id == 'SEMANTIC-FE-001'
    ]


def _make_code_yaml(code_content: str | None = 'return 1', code_in_params: bool = True) -> str:
    if code_in_params and code_content is not None:
        code_section = f"""
        codeParam:
          - name: code
            input:
              type: string
              value:
                type: literal
                content: '{code_content}'"""
    elif code_in_params and code_content is None:
        code_section = """
        codeParam: []"""
    else:
        code_section = ""

    return f"""
nodes:
  - id: '100001'
    type: '1'
    data:
      nodeMeta:
        title: Start
  - id: 'c1'
    type: '5'
    data:
      nodeMeta:
        title: Code
      inputs:
        inputParameters: []{code_section}
  - id: '900001'
    type: '2'
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: '100001'
    targetNodeID: 'c1'
  - sourceNodeID: 'c1'
    targetNodeID: '900001'
"""


# ── Positive ─────────────────────────────────────────────────────

class TestFE001_Code_Positive:
    """Valid code configurations → no FE-001 errors."""

    def test_with_code_content(self):
        yaml = _make_code_yaml(code_content='return 1')
        errors = _fe001_errors(yaml)
        assert not any('code' in e.lower() for e in errors)

    def test_multiline_code(self):
        yaml = _make_code_yaml(code_content='def f():\\n  return 42')
        errors = _fe001_errors(yaml)
        assert not any('code' in e.lower() for e in errors)

    def test_code_with_loop(self):
        """Code with a loop construct → valid."""
        yaml = _make_code_yaml(code_content='for i in range(10):\\n  print(i)')
        errors = _fe001_errors(yaml)
        assert not any('code' in e.lower() for e in errors)

    def test_code_with_imports(self):
        """Code with import statement → valid."""
        yaml = _make_code_yaml(code_content='import json\\nreturn json.dumps({})')
        errors = _fe001_errors(yaml)
        assert not any('code' in e.lower() for e in errors)


# ── Negative ─────────────────────────────────────────────────────

class TestFE001_Code_Negative:
    """Invalid code configurations → FE-001 errors."""

    def test_missing_code_param(self):
        yaml = _make_code_yaml(code_content=None)
        errors = _fe001_errors(yaml)
        assert any('code' in e.lower() for e in errors)

    def test_empty_code_string(self):
        yaml = _make_code_yaml(code_content='')
        errors = _fe001_errors(yaml)
        assert any('code' in e.lower() for e in errors)

    def test_whitespace_only_code(self):
        yaml = _make_code_yaml(code_content='   ')
        errors = _fe001_errors(yaml)
        assert any('code' in e.lower() for e in errors)

    def test_no_code_section_at_all(self):
        yaml = _make_code_yaml(code_content=None, code_in_params=False)
        errors = _fe001_errors(yaml)
        assert any('code' in e.lower() for e in errors)


# ── Edge cases ──────────────────────────────────────────────────

class TestFE001_Code_EdgeCases:
    """Edge cases for code node validation."""

    def test_code_with_special_characters(self):
        """Code containing special chars → valid."""
        yaml = _make_code_yaml(code_content='x = "hello\\nworld"')
        errors = _fe001_errors(yaml)
        assert not any('code' in e.lower() for e in errors)

    def test_two_code_nodes_one_empty(self):
        """Two code nodes: one valid, one empty → error for empty."""
        yaml = """
nodes:
  - id: '100001'
    type: '1'
    data:
      nodeMeta:
        title: Start
  - id: 'c1'
    type: '5'
    data:
      nodeMeta:
        title: Code1
      inputs:
        inputParameters: []
        codeParam:
          - name: code
            input:
              type: string
              value:
                type: literal
                content: 'return 1'
  - id: 'c2'
    type: '5'
    data:
      nodeMeta:
        title: Code2
      inputs:
        inputParameters: []
        codeParam: []
  - id: '900001'
    type: '2'
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: '100001'
    targetNodeID: 'c1'
  - sourceNodeID: 'c1'
    targetNodeID: 'c2'
  - sourceNodeID: 'c2'
    targetNodeID: '900001'
"""
        errors = _fe001_errors(yaml)
        assert any('code' in e.lower() for e in errors)
