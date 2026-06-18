"""FE-001: Dataset 节点 (types 6/27) 字段验证。

验证规则:
  - knowledge 必填 (必须选择知识库)
"""

import pytest

from tests.conftest import compile_text


def _fe001_errors(yaml_text: str) -> list[str]:
    report = compile_text(yaml_text)
    return [
        d.message for d in report.diagnostics
        if d.rule_id == 'SEMANTIC-FE-001'
    ]


def _make_dataset_yaml(
    node_type: str = '6',
    knowledge: str | None = 'kb-123',
) -> str:
    knowledge_section = ""
    if knowledge is not None:
        knowledge_section = f"""
        knowledge: '{knowledge}'"""

    # Add required inputParameter based on node type
    if node_type == '6':
        input_params = """
          - name: 'Query'
            input:
              type: 'literal'
              content: 'test query'"""
    elif node_type == '27':
        input_params = """
          - name: 'knowledge'
            input:
              type: 'literal'
              content: 'ref'"""
    else:
        input_params = ""

    return f"""
nodes:
  - id: '100001'
    type: '1'
    data:
      nodeMeta:
        title: Start
  - id: 'ds1'
    type: '{node_type}'
    data:
      nodeMeta:
        title: Dataset
      inputs:
        inputParameters:
          {input_params}{knowledge_section}
  - id: '900001'
    type: '2'
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: '100001'
    targetNodeID: 'ds1'
  - sourceNodeID: 'ds1'
    targetNodeID: '900001'
"""


# ── Positive ─────────────────────────────────────────────────────

class TestFE001_Dataset_Positive:
    def test_with_knowledge(self):
        yaml = _make_dataset_yaml(knowledge='kb-123')
        errors = _fe001_errors(yaml)
        assert not any('knowledge' in e.lower() for e in errors)

    @pytest.mark.parametrize("type_id", ['6', '27'])
    def test_both_types_ok(self, type_id):
        yaml = _make_dataset_yaml(node_type=type_id, knowledge='kb-123')
        errors = _fe001_errors(yaml)
        assert not any('knowledge' in e.lower() for e in errors)


# ── Negative ─────────────────────────────────────────────────────

class TestFE001_Dataset_Negative:
    def test_missing_knowledge(self):
        yaml = _make_dataset_yaml(knowledge=None)
        errors = _fe001_errors(yaml)
        assert any('knowledge' in e.lower() for e in errors)

    def test_empty_knowledge(self):
        yaml = _make_dataset_yaml(knowledge='')
        errors = _fe001_errors(yaml)
        assert any('knowledge' in e.lower() for e in errors)

    @pytest.mark.parametrize("type_id", ['6', '27'])
    def test_both_types_require_knowledge(self, type_id):
        yaml = _make_dataset_yaml(node_type=type_id, knowledge=None)
        errors = _fe001_errors(yaml)
        assert any('knowledge' in e.lower() for e in errors)


# ── P2: inputParameters required checks ──────────────────────────

def _make_dataset_search_yaml(query_param: bool = True) -> str:
    qp = """
          - name: 'Query'
            input:
              type: 'literal'
              content: 'test query'""" if query_param else " []"
    return f"""
nodes:
  - id: '100001'
    type: '1'
    data:
      nodeMeta:
        title: Start
  - id: 'ds1'
    type: '6'
    data:
      nodeMeta:
        title: DatasetSearch
      inputs:
        inputParameters:{qp}
        datasetParam:
          datasetInfoList:
            - id: 'kb1'
  - id: '900001'
    type: '2'
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: '100001'
    targetNodeID: 'ds1'
  - sourceNodeID: 'ds1'
    targetNodeID: '900001'
"""


def _make_dataset_write_yaml(knowledge_input: bool = True) -> str:
    kp = """
          - name: 'knowledge'
            input:
              type: 'literal'
              content: 'ref'""" if knowledge_input else " []"
    return f"""
nodes:
  - id: '100001'
    type: '1'
    data:
      nodeMeta:
        title: Start
  - id: 'ds1'
    type: '27'
    data:
      nodeMeta:
        title: DatasetWrite
      inputs:
        inputParameters:{kp}
        knowledge: 'kb-123'
        datasetWriteParam:
          datasetInfoList:
            - id: 'kb1'
  - id: '900001'
    type: '2'
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: '100001'
    targetNodeID: 'ds1'
  - sourceNodeID: 'ds1'
    targetNodeID: '900001'
"""


class TestFE001_DatasetSearch_Query:
    def test_with_query_param(self):
        errors = _fe001_errors(_make_dataset_search_yaml(query_param=True))
        assert not any('Query' in e for e in errors)

    def test_missing_query_param(self):
        errors = _fe001_errors(_make_dataset_search_yaml(query_param=False))
        assert any('Query' in e for e in errors)


class TestFE001_DatasetWrite_KnowledgeInput:
    def test_with_knowledge_input(self):
        errors = _fe001_errors(_make_dataset_write_yaml(knowledge_input=True))
        assert not any('knowledge input' in e.lower() for e in errors)

    def test_missing_knowledge_input(self):
        errors = _fe001_errors(_make_dataset_write_yaml(knowledge_input=False))
        assert any('knowledge input' in e.lower() for e in errors)
