"""TRANSPORT-001/002: Parse error recovery tests.

Verify that YAML/JSON syntax errors are captured as Diagnostics
instead of raising Python exceptions.
"""
import pytest
from tests.conftest import compile_text


class TestTransportJsonError:
    """TRANSPORT-001: JSON syntax error recovery."""

    def test_json_syntax_error_captured(self):
        """Malformed JSON should produce TRANSPORT-001 diagnostic."""
        json_text = '{"nodes": [invalid json'
        report = compile_text(json_text)
        transport_diag = [d for d in report.diagnostics if d.rule_id == 'TRANSPORT-001']
        assert len(transport_diag) == 1, f"Expected TRANSPORT-001, got: {report.diagnostics}"
        assert 'syntax error' in transport_diag[0].message.lower()

    def test_json_missing_bracket(self):
        """JSON with unclosed bracket should produce TRANSPORT-001."""
        json_text = '{"nodes": [{"id": "100001", "type": "1"'
        report = compile_text(json_text)
        transport_diag = [d for d in report.diagnostics if d.rule_id == 'TRANSPORT-001']
        assert len(transport_diag) == 1


class TestTransportYamlError:
    """TRANSPORT-002: YAML syntax error recovery."""

    def test_yaml_syntax_error_captured(self):
        """Malformed YAML should produce TRANSPORT-002 diagnostic."""
        yaml_text = """
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta:
        title: Start
      bad_indent:
        this line has wrong indentation
   this is definitely wrong
"""
        report = compile_text(yaml_text)
        transport_diag = [d for d in report.diagnostics if d.rule_id == 'TRANSPORT-002']
        assert len(transport_diag) >= 1, f"Expected TRANSPORT-002, got: {report.diagnostics}"

    def test_yaml_bad_mapping(self):
        """YAML with invalid mapping should produce TRANSPORT-002."""
        yaml_text = """
nodes:
  - id: "100001"
    type: "1"
    data: {bad: [unclosed
"""
        report = compile_text(yaml_text)
        transport_diag = [d for d in report.diagnostics if d.rule_id == 'TRANSPORT-002']
        assert len(transport_diag) >= 1


class TestTransportValidPassthrough:
    """Valid documents should pass through without transport errors."""

    def test_valid_json_no_transport_error(self):
        json_text = '{"nodes": [{"id": "100001", "type": "1", "data": {"nodeMeta": {"title": "Start"}}}], "edges": []}'
        report = compile_text(json_text)
        transport_diag = [d for d in report.diagnostics if d.rule_id.startswith('TRANSPORT-')]
        assert len(transport_diag) == 0, f"Unexpected transport errors: {transport_diag}"

    def test_valid_yaml_no_transport_error(self):
        yaml_text = """
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta:
        title: Start
edges: []
"""
        report = compile_text(yaml_text)
        transport_diag = [d for d in report.diagnostics if d.rule_id.startswith('TRANSPORT-')]
        assert len(transport_diag) == 0, f"Unexpected transport errors: {transport_diag}"
