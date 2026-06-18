"""Boundary tests for BE-015: cycle detection."""
from tests.conftest import compile_text


def _be015(yaml_text):
    return 'SEMANTIC-BE-015' in [d.rule_id for d in compile_text(yaml_text).diagnostics]


class TestCycleBoundary:
    """Cycle detection boundary tests."""

    def test_no_cycle_ok(self):
        """Linear chain A→B→C has no cycle."""
        yaml = """
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta: {title: Start}
  - id: "n2"
    type: "3"
    data:
      nodeMeta: {title: LLM}
      inputs:
        inputParameters:
          - name: prompt
            input: {type: string, value: {type: literal, content: hi}}
  - id: "900001"
    type: "2"
    data:
      nodeMeta: {title: End}
edges:
  - sourceNodeID: "100001"
    targetNodeID: "n2"
  - sourceNodeID: "n2"
    targetNodeID: "900001"
"""
        assert not _be015(yaml)

    def test_two_node_cycle(self):
        """A→B→A is a cycle."""
        yaml = """
nodes:
  - id: "n1"
    type: "3"
    data:
      nodeMeta: {title: LLM1}
      inputs:
        inputParameters:
          - name: prompt
            input: {type: string, value: {type: literal, content: hi}}
  - id: "n2"
    type: "3"
    data:
      nodeMeta: {title: LLM2}
      inputs:
        inputParameters:
          - name: prompt
            input: {type: string, value: {type: literal, content: hi}}
edges:
  - sourceNodeID: "n1"
    targetNodeID: "n2"
  - sourceNodeID: "n2"
    targetNodeID: "n1"
"""
        assert _be015(yaml)

    def test_diamond_no_cycle(self):
        """Diamond A→B, A→C, B→D, C→D has no cycle."""
        yaml = """
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta: {title: Start}
  - id: "b"
    type: "3"
    data:
      nodeMeta: {title: LLM_B}
      inputs:
        inputParameters:
          - name: prompt
            input: {type: string, value: {type: literal, content: b}}
  - id: "c"
    type: "3"
    data:
      nodeMeta: {title: LLM_C}
      inputs:
        inputParameters:
          - name: prompt
            input: {type: string, value: {type: literal, content: c}}
  - id: "900001"
    type: "2"
    data:
      nodeMeta: {title: End}
edges:
  - sourceNodeID: "100001"
    targetNodeID: "b"
  - sourceNodeID: "100001"
    targetNodeID: "c"
  - sourceNodeID: "b"
    targetNodeID: "900001"
  - sourceNodeID: "c"
    targetNodeID: "900001"
"""
        assert not _be015(yaml)
