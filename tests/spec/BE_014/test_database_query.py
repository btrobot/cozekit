"""BE-014: Database node validation (FE-001 sub-check)."""
from tests.conftest import compile_text


class TestDatabaseFields:
    def test_database_with_sql_ok(self):
        yaml = """
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta: {title: Start}
  - id: "d1"
    type: "12"
    data:
      nodeMeta: {title: Database}
      inputs:
        sql: "SELECT * FROM users"
        databaseInfoList:
          - databaseId: "db1"
    outputs:
      - name: result
        type: object
  - id: "900001"
    type: "2"
    data:
      nodeMeta: {title: End}
edges:
  - sourceNodeID: "100001"
    targetNodeID: "d1"
  - sourceNodeID: "d1"
    targetNodeID: "900001"
"""
        report = compile_text(yaml)
        db_errors = [d for d in report.diagnostics
                      if d.rule_id == 'SEMANTIC-FE-001' and 'Database' in d.message]
        assert len(db_errors) == 0

    def test_database_without_sql_violation(self):
        yaml = """
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta: {title: Start}
  - id: "d1"
    type: "12"
    data:
      nodeMeta: {title: Database}
  - id: "900001"
    type: "2"
    data:
      nodeMeta: {title: End}
edges:
  - sourceNodeID: "100001"
    targetNodeID: "d1"
  - sourceNodeID: "d1"
    targetNodeID: "900001"
"""
        report = compile_text(yaml)
        db_errors = [d for d in report.diagnostics
                      if d.rule_id == 'SEMANTIC-FE-001' and 'Database' in d.message]
        assert len(db_errors) >= 1
