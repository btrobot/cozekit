"""Boundary tests for FE-009/010/011: title validation."""
from tests.conftest import compile_text


def _fe_ids(yaml_text):
    return sorted(d.rule_id for d in compile_text(yaml_text).diagnostics)


class TestFE009_Boundary:
    """Title required boundary tests."""

    def test_empty_title_fe009(self):
        """Empty string title triggers FE-009."""
        yaml = """
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta:
        title: ""
  - id: "900001"
    type: "2"
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: "100001"
    targetNodeID: "900001"
"""
        assert 'SEMANTIC-FE-009' in _fe_ids(yaml)

    def test_single_char_title_ok(self):
        """Single character title is valid."""
        yaml = """
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta:
        title: "A"
  - id: "900001"
    type: "2"
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: "100001"
    targetNodeID: "900001"
"""
        assert 'SEMANTIC-FE-009' not in _fe_ids(yaml)

    def test_unicode_title_ok(self):
        """Unicode title is valid."""
        yaml = """
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta:
        title: "开始节点"
  - id: "900001"
    type: "2"
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: "100001"
    targetNodeID: "900001"
"""
        assert 'SEMANTIC-FE-009' not in _fe_ids(yaml)


class TestFE010_Boundary:
    """Title max length boundary tests."""

    def test_title_63_chars_ok(self):
        """Title at exactly 63 characters is valid."""
        yaml = f"""
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta:
        title: '{"a" * 63}'
  - id: "900001"
    type: "2"
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: "100001"
    targetNodeID: "900001"
"""
        assert 'SEMANTIC-FE-010' not in _fe_ids(yaml)

    def test_title_64_chars_violation(self):
        """Title at 64 characters triggers FE-010."""
        yaml = f"""
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta:
        title: '{"a" * 64}'
  - id: "900001"
    type: "2"
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: "100001"
    targetNodeID: "900001"
"""
        assert 'SEMANTIC-FE-010' in _fe_ids(yaml)


class TestFE011_Boundary:
    """Title uniqueness boundary tests."""

    def test_duplicate_titles_fe011(self):
        """Two nodes with same title triggers FE-011."""
        yaml = """
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta:
        title: "Same"
  - id: "n2"
    type: "3"
    data:
      nodeMeta:
        title: "Same"
      inputs:
        inputParameters:
          - name: prompt
            input:
              type: string
              value: hello
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
        assert 'SEMANTIC-FE-011' in _fe_ids(yaml)

    def test_unique_titles_ok(self):
        """Different titles produce no FE-011."""
        yaml = """
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta:
        title: "Start"
  - id: "900001"
    type: "2"
    data:
      nodeMeta:
        title: "End"
edges:
  - sourceNodeID: "100001"
    targetNodeID: "900001"
"""
        assert 'SEMANTIC-FE-011' not in _fe_ids(yaml)
