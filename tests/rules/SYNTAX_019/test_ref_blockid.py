"""SYNTAX-019: ref must have blockID (except literals and global vars)."""
from tests.conftest import compile_text


def _syntax019(yaml_text):
    return 'SYNTAX-019' in [d.rule_id for d in compile_text(yaml_text).diagnostics]


class TestSyntax019Positive:
    """Ref with blockID → no SYNTAX-019."""

    def test_ref_with_blockid_ok(self):
        yaml = """
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta:
        title: Start
      outputs:
        - name: out1
          type: string
  - id: "n2"
    type: "3"
    data:
      nodeMeta:
        title: LLM
      inputs:
        inputParameters:
          - name: prompt
            input:
              type: string
              value:
                type: ref
                content:
                  source: node
                  blockID: "100001"
                  name: out1
  - id: "900001"
    type: "2"
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: "100001"
    targetNodeID: "n2"
  - sourceNodeID: "n2"
    targetNodeID: "900001"
"""
        assert not _syntax019(yaml)

    def test_literal_ref_ok(self):
        """Literal ref has no blockID requirement."""
        yaml = """
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta:
        title: Start
  - id: "n2"
    type: "3"
    data:
      nodeMeta:
        title: LLM
      inputs:
        inputParameters:
          - name: prompt
            input:
              type: string
              value:
                type: literal
                content: hello
  - id: "900001"
    type: "2"
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: "100001"
    targetNodeID: "n2"
  - sourceNodeID: "n2"
    targetNodeID: "900001"
"""
        assert not _syntax019(yaml)

    def test_global_var_ref_ok(self):
        """Global variable ref has no blockID requirement."""
        yaml = """
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta:
        title: Start
  - id: "n2"
    type: "3"
    data:
      nodeMeta:
        title: LLM
      inputs:
        inputParameters:
          - name: prompt
            input:
              type: string
              value:
                type: ref
                content:
                  source: global_variable_app
                  name: myVar
  - id: "900001"
    type: "2"
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: "100001"
    targetNodeID: "n2"
  - sourceNodeID: "n2"
    targetNodeID: "900001"
"""
        assert not _syntax019(yaml)


class TestSyntax019Negative:
    """Ref without blockID → SYNTAX-019."""

    def test_ref_without_blockid_violation(self):
        """Ref with source=node but empty blockID triggers SYNTAX-019."""
        yaml = """
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta:
        title: Start
  - id: "n2"
    type: "3"
    data:
      nodeMeta:
        title: LLM
      inputs:
        inputParameters:
          - name: prompt
            input:
              type: string
              value:
                type: ref
                content:
                  source: node
                  blockID: ""
                  name: out1
  - id: "900001"
    type: "2"
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: "100001"
    targetNodeID: "n2"
  - sourceNodeID: "n2"
    targetNodeID: "900001"
"""
        assert _syntax019(yaml)

    def test_ref_missing_blockid_violation(self):
        """Ref with source=node but no blockID field triggers SYNTAX-019."""
        yaml = """
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta:
        title: Start
  - id: "n2"
    type: "3"
    data:
      nodeMeta:
        title: LLM
      inputs:
        inputParameters:
          - name: prompt
            input:
              type: string
              value:
                type: ref
                content:
                  source: node
                  name: out1
  - id: "900001"
    type: "2"
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: "100001"
    targetNodeID: "n2"
  - sourceNodeID: "n2"
    targetNodeID: "900001"
"""
        assert _syntax019(yaml)
