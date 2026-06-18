"""BE-012: Variable merge node requires mergeGroups (FE-001 sub-check)."""
from tests.conftest import compile_text


class TestVariableMergeFields:
    def test_merge_with_mergegroups_ok(self):
        yaml = """
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta: {title: Start}
  - id: "m1"
    type: "32"
    data:
      nodeMeta: {title: Merge}
      inputs:
        mergeGroups:
          - name: group1
            input:
              type: string
              value: {type: literal, content: hello}
  - id: "900001"
    type: "2"
    data:
      nodeMeta: {title: End}
edges:
  - sourceNodeID: "100001"
    targetNodeID: "m1"
  - sourceNodeID: "m1"
    targetNodeID: "900001"
"""
        report = compile_text(yaml)
        merge_errors = [d for d in report.diagnostics
                        if d.rule_id == 'SEMANTIC-FE-001' and 'VariableMerge' in d.message]
        assert len(merge_errors) == 0

    def test_merge_without_mergegroups_violation(self):
        yaml = """
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta: {title: Start}
  - id: "m1"
    type: "32"
    data:
      nodeMeta: {title: Merge}
  - id: "900001"
    type: "2"
    data:
      nodeMeta: {title: End}
edges:
  - sourceNodeID: "100001"
    targetNodeID: "m1"
  - sourceNodeID: "m1"
    targetNodeID: "900001"
"""
        report = compile_text(yaml)
        merge_errors = [d for d in report.diagnostics
                        if d.rule_id == 'SEMANTIC-FE-001' and 'VariableMerge' in d.message]
        assert len(merge_errors) >= 1
