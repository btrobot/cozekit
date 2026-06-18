"""P2-3: Type flow analysis tests.

Verify type compatibility checking through ref chains:
A.output → B.input → C.input
"""
import pytest
from tests.conftest import compile_text


def _be021_count(yaml_text: str) -> int:
    return len([d for d in compile_text(yaml_text).diagnostics if d.rule_id == 'SEMANTIC-BE-021'])


class TestTypeFlow:
    """Type flow analysis: track types through ref chains."""

    def test_direct_type_mismatch_detected(self):
        """A(output:integer) → B(input:string ref A) → BE-021."""
        yaml = """
schema_version: 1.0.0
name: test_type_flow
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
                value: test
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
edges:
    - sourceNodeID: "100001"
      targetNodeID: "n2"
    - sourceNodeID: "n2"
      targetNodeID: "900001"
"""
        assert _be021_count(yaml) >= 1

    def test_same_type_no_warning(self):
        """A(output:string) → B(input:string ref A) → no BE-021."""
        yaml = """
schema_version: 1.0.0
name: test_type_flow
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
                value: test
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
edges:
    - sourceNodeID: "100001"
      targetNodeID: "n2"
    - sourceNodeID: "n2"
      targetNodeID: "900001"
"""
        assert _be021_count(yaml) == 0

    def test_global_var_ref_skipped(self):
        """Global variable refs produce no type mismatch."""
        yaml = """
schema_version: 1.0.0
name: test_global
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
                value: test
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
        assert _be021_count(yaml) == 0

    def test_unknown_type_no_error(self):
        """Unknown types produce no false positive."""
        yaml = """
schema_version: 1.0.0
name: test_unknown
id: "100"
mode: workflow
nodes:
    - id: "100001"
      type: start
      title: Start
      parameters:
        node_outputs:
            out1:
                type: custom_object
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
                value: test
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
edges:
    - sourceNodeID: "100001"
      targetNodeID: "n2"
    - sourceNodeID: "n2"
      targetNodeID: "900001"
"""
        assert _be021_count(yaml) == 0

    def test_no_ref_params_skipped(self):
        """Parameters without refs produce no BE-021."""
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
                value: hello world
            - name: systemPrompt
              input:
                type: string
                value: test
    - id: "900001"
      type: end
      title: End
edges:
    - sourceNodeID: "100001"
      targetNodeID: "n2"
    - sourceNodeID: "n2"
      targetNodeID: "900001"
"""
        assert _be021_count(yaml) == 0
