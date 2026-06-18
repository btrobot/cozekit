"""BE-013: Code node validation (FE-001 sub-check)."""
from tests.conftest import compile_text


class TestCodeFields:
    def test_code_with_content_ok(self):
        yaml = """
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta: {title: Start}
  - id: "c1"
    type: "5"
    data:
      nodeMeta: {title: Code}
      inputs:
        code: "print('hello')"
        language: "python3"
  - id: "900001"
    type: "2"
    data:
      nodeMeta: {title: End}
edges:
  - sourceNodeID: "100001"
    targetNodeID: "c1"
  - sourceNodeID: "c1"
    targetNodeID: "900001"
"""
        report = compile_text(yaml)
        code_errors = [d for d in report.diagnostics
                        if d.rule_id == 'SEMANTIC-FE-001' and 'Code' in d.message]
        assert len(code_errors) == 0

    def test_code_without_content_violation(self):
        yaml = """
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta: {title: Start}
  - id: "c1"
    type: "5"
    data:
      nodeMeta: {title: Code}
  - id: "900001"
    type: "2"
    data:
      nodeMeta: {title: End}
edges:
  - sourceNodeID: "100001"
    targetNodeID: "c1"
  - sourceNodeID: "c1"
    targetNodeID: "900001"
"""
        report = compile_text(yaml)
        code_errors = [d for d in report.diagnostics
                        if d.rule_id == 'SEMANTIC-FE-001' and 'Code' in d.message]
        assert len(code_errors) >= 1
