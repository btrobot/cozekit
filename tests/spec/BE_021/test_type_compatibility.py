"""BE-021: Type compatibility for parameter assignments."""
import pytest
from tests.conftest import compile_text


# YAML source format template: start → LLM → end
# The LLM node has an input ref from the start node's output
_YAML_SAME_TYPE = """
schema_version: 1.0.0
name: test_compat
id: "100"
mode: workflow
nodes:
    - id: "100001"
      type: start
      title: Start
      parameters:
        node_outputs:
            out1:
                type: string
                value: null
    - id: "n2"
      type: llm
      title: LLM
      parameters:
        llmParam:
            - name: modelType
              input:
                type: integer
                value: "1"
            - name: prompt
              input:
                type: string
                value: ""
            - name: systemPrompt
              input:
                type: string
                value: ""
        node_inputs:
            - name: target
              input:
                type: string
                value:
                    path: out1
                    ref_node: "100001"
    - id: "900001"
      type: end
      title: End
      parameters:
        content:
            type: string
            value:
                content: "{{output}}"
                type: literal
        node_inputs:
            - name: output
              input:
                type: string
                value:
                    path: target
                    ref_node: "n2"
edges:
    - sourceNodeID: "100001"
      targetNodeID: "n2"
    - sourceNodeID: "n2"
      targetNodeID: "900001"
"""

# Incompatible type: start output is integer, LLM input expects string
_YAML_DIFF_TYPE = """
schema_version: 1.0.0
name: test_compat
id: "100"
mode: workflow
nodes:
    - id: "100001"
      type: start
      title: Start
      parameters:
        node_outputs:
            out1:
                type: integer
                value: null
    - id: "n2"
      type: llm
      title: LLM
      parameters:
        llmParam:
            - name: modelType
              input:
                type: integer
                value: "1"
            - name: prompt
              input:
                type: string
                value: ""
            - name: systemPrompt
              input:
                type: string
                value: ""
        node_inputs:
            - name: target
              input:
                type: string
                value:
                    path: out1
                    ref_node: "100001"
    - id: "900001"
      type: end
      title: End
      parameters:
        content:
            type: string
            value:
                content: "{{output}}"
                type: literal
        node_inputs:
            - name: output
              input:
                type: string
                value:
                    path: target
                    ref_node: "n2"
edges:
    - sourceNodeID: "100001"
      targetNodeID: "n2"
    - sourceNodeID: "n2"
      targetNodeID: "900001"
"""


class TestTypeCompatibility:
    """Tests for SEMANTIC-BE-021 type mismatch detection."""

    def test_compatible_same_type_no_warning(self):
        """Same type ref (string→string) should produce no BE-021 warning."""
        report = compile_text(_YAML_SAME_TYPE)
        be021 = [d for d in report.diagnostics if 'BE-021' in d.rule_id]
        assert len(be021) == 0, f"Expected no BE-021, got: {be021}"

    def test_incompatible_types_warning(self):
        """Different type ref (integer→string) should produce BE-021 warning."""
        report = compile_text(_YAML_DIFF_TYPE)
        be021 = [d for d in report.diagnostics if 'BE-021' in d.rule_id]
        assert len(be021) >= 1, f"Expected BE-021 for integer→string mismatch, got: {[d.rule_id for d in report.diagnostics]}"

    def test_no_ref_skipped(self):
        """Parameters without refs should not trigger BE-021."""
        yaml = """
schema_version: 1.0.0
name: test_no_ref
id: "100"
mode: workflow
nodes:
    - id: "100001"
      type: start
      title: Start
    - id: "n2"
      type: llm
      title: LLM
      parameters:
        llmParam:
            - name: modelType
              input:
                type: integer
                value: "1"
            - name: prompt
              input:
                type: string
                value: hello
            - name: systemPrompt
              input:
                type: string
                value: ""
    - id: "900001"
      type: end
      title: End
edges:
    - sourceNodeID: "100001"
      targetNodeID: "n2"
    - sourceNodeID: "n2"
      targetNodeID: "900001"
"""
        report = compile_text(yaml)
        be021 = [d for d in report.diagnostics if 'BE-021' in d.rule_id]
        assert len(be021) == 0, f"Expected no BE-021, got: {be021}"

    def test_global_var_ref_skipped(self):
        """Global variable refs should be skipped (runtime-deferred)."""
        yaml = """
schema_version: 1.0.0
name: test_global_ref
id: "100"
mode: workflow
nodes:
    - id: "100001"
      type: start
      title: Start
    - id: "n2"
      type: llm
      title: LLM
      parameters:
        llmParam:
            - name: modelType
              input:
                type: integer
                value: "1"
            - name: prompt
              input:
                type: string
                value: ""
            - name: systemPrompt
              input:
                type: string
                value: ""
        node_inputs:
            - name: target
              input:
                value:
                    path: myVar
                    ref_node: "global_variable_app"
    - id: "900001"
      type: end
      title: End
edges:
    - sourceNodeID: "100001"
      targetNodeID: "n2"
    - sourceNodeID: "n2"
      targetNodeID: "900001"
"""
        report = compile_text(yaml)
        be021 = [d for d in report.diagnostics if 'BE-021' in d.rule_id]
        assert len(be021) == 0, f"Expected no BE-021 for global var ref, got: {be021}"
