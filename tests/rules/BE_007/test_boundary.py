"""Boundary tests for BE-007: isolated nodes."""
from tests.conftest import compile_text


def _be007(yaml_text):
    return 'SEMANTIC-BE-007' in [d.rule_id for d in compile_text(yaml_text).diagnostics]


class TestIsolatedBoundary:
    """Isolated node detection boundary tests."""

    def test_connected_node_ok(self):
        """Node with edge is not isolated."""
        yaml = """
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta: {title: Start}
  - id: "900001"
    type: "2"
    data:
      nodeMeta: {title: End}
edges:
  - sourceNodeID: "100001"
    targetNodeID: "900001"
"""
        assert not _be007(yaml)

    def test_isolated_node_violation(self):
        """Node with no edges triggers BE-007."""
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
    targetNodeID: "900001"
"""
        assert _be007(yaml)

    def test_comment_node_exemption(self):
        """Comment node without edges is exempt from BE-007."""
        yaml = """
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta: {title: Start}
  - id: "c1"
    type: "31"
    data:
      nodeMeta: {title: My Comment}
  - id: "900001"
    type: "2"
    data:
      nodeMeta: {title: End}
edges:
  - sourceNodeID: "100001"
    targetNodeID: "900001"
"""
        assert not _be007(yaml)
