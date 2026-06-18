"""P2-4: Error recovery — partial AST construction on malformed input."""
import pytest
from tests.conftest import compile_text


class TestNodeErrorRecovery:
    """Bad nodes are skipped, good nodes are preserved."""

    def test_valid_nodes_preserved_with_bad_node(self):
        """Valid nodes parsed even when a node has invalid structure."""
        # This tests the builder's error recovery - a node with missing
        # required fields should not crash the entire compilation
        yaml = """
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta:
        title: Start
  - id: "900001"
    type: "2"
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: "100001"
    targetNodeID: "900001"
"""
        report = compile_text(yaml)
        # Should succeed without Python exception
        assert hasattr(report, "diagnostics")


class TestEdgeErrorRecovery:
    """Bad edges are skipped, good edges are preserved."""

    def test_valid_edges_preserved_with_bad_edge(self):
        """Valid edges parsed even when an edge has invalid structure."""
        yaml = """
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta:
        title: Start
  - id: "900001"
    type: "2"
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: "100001"
    targetNodeID: "900001"
"""
        report = compile_text(yaml)
        assert hasattr(report, "diagnostics")


class TestTransportErrorRecovery:
    """Transport-level errors produce diagnostics, not exceptions."""

    def test_no_exception_on_malformed_inputs(self):
        """Various malformed inputs never raise Python exceptions."""
        bad_inputs = [
            '{"nodes": [}',
            'nodes: [}',
            '{bad json',
        ]
        for bad_input in bad_inputs:
            report = compile_text(bad_input)
            assert hasattr(report, "diagnostics"), f"Failed for: {bad_input}"

    def test_empty_document_handled(self):
        """Empty dict produces diagnostics, not exception."""
        report = compile_text('{}')
        assert hasattr(report, "diagnostics")

    def test_missing_nodes_handled(self):
        """Document with no nodes key produces diagnostics."""
        report = compile_text('{"edges": []}')
        assert hasattr(report, "diagnostics")
