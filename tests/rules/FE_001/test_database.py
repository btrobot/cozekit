"""FE-001: Database 节点 (types 12/42/43/44/46) 字段验证。

验证规则:
  - sql 必填 (SQL 语句不能为空)
  - databaseInfoList 必填 (必须选择数据库)
  - queryLimit 范围 [1, 1000] (仅 DatabaseQuery type=43)

Tests cover:
  - Valid SQL and database info
  - Missing SQL
  - Empty SQL
  - Missing databaseInfoList
  - Empty databaseInfoList
  - Query limit in range
  - Query limit out of range (too low, too high)
  - Multiple database types (12, 42, 43, 44, 46)
  - SQL with special characters
"""

import pytest

from tests.conftest import compile_text


def _fe001_errors(yaml_text: str) -> list[str]:
    report = compile_text(yaml_text)
    return [
        d.message for d in report.diagnostics
        if d.rule_id == 'SEMANTIC-FE-001'
    ]


def _make_database_yaml(
    node_type: str = '12',
    sql: str | None = 'SELECT * FROM users',
    db_info: str = '[{id: db-1}]',
    limit: str | None = None,
) -> str:
    parts = [
        "        inputParameters: []",
    ]
    if sql is not None:
        parts.append(f"        sql: '{sql}'")
    parts.append(f"        databaseInfoList: {db_info}")
    if limit is not None:
        parts.append(f"        selectParam:\n          limit: {limit}")

    inputs_block = '\n'.join(parts)

    return f"""
nodes:
  - id: '100001'
    type: '1'
    data:
      nodeMeta:
        title: Start
  - id: 'db1'
    type: '{node_type}'
    data:
      nodeMeta:
        title: Database
      inputs:
{inputs_block}
  - id: '900001'
    type: '2'
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: '100001'
    targetNodeID: 'db1'
  - sourceNodeID: 'db1'
    targetNodeID: '900001'
"""


# ── Positive ─────────────────────────────────────────────────────

class TestFE001_Database_Positive:
    """Valid database configurations → no FE-001 errors."""

    def test_with_sql_and_db(self):
        yaml = _make_database_yaml()
        errors = _fe001_errors(yaml)
        assert not any('sql' in e.lower() for e in errors)
        assert not any('database' in e.lower() for e in errors)

    def test_query_limit_in_range(self):
        """queryLimit 500 → no error."""
        yaml = _make_database_yaml(node_type='43', limit='500')
        errors = _fe001_errors(yaml)
        assert not any('limit' in e.lower() for e in errors)

    def test_query_limit_at_min(self):
        """queryLimit 1 → no error."""
        yaml = _make_database_yaml(node_type='43', limit='1')
        errors = _fe001_errors(yaml)
        assert not any('limit' in e.lower() for e in errors)

    def test_query_limit_at_max(self):
        """queryLimit 1000 → no error."""
        yaml = _make_database_yaml(node_type='43', limit='1000')
        errors = _fe001_errors(yaml)
        assert not any('limit' in e.lower() for e in errors)

    @pytest.mark.parametrize("type_id", ['12', '42', '43', '44', '46'])
    def test_all_db_types_valid(self, type_id):
        """All database subtypes with valid SQL → no errors."""
        yaml = _make_database_yaml(node_type=type_id)
        errors = _fe001_errors(yaml)
        assert not any('sql' in e.lower() for e in errors)


# ── Negative ─────────────────────────────────────────────────────

class TestFE001_Database_Negative:
    """Invalid database configurations → FE-001 errors."""

    def test_missing_sql(self):
        yaml = _make_database_yaml(sql=None)
        errors = _fe001_errors(yaml)
        assert any('sql' in e.lower() for e in errors)

    def test_empty_sql(self):
        yaml = _make_database_yaml(sql='')
        errors = _fe001_errors(yaml)
        assert any('sql' in e.lower() for e in errors)

    def test_missing_database_info(self):
        yaml = _make_database_yaml(db_info='[]')
        errors = _fe001_errors(yaml)
        assert any('database' in e.lower() for e in errors)

    def test_query_limit_zero(self):
        """queryLimit 0 → out of range error."""
        yaml = _make_database_yaml(node_type='43', limit='0')
        errors = _fe001_errors(yaml)
        assert any('limit' in e.lower() for e in errors)

    def test_query_limit_over_max(self):
        """queryLimit 1001 → out of range error."""
        yaml = _make_database_yaml(node_type='43', limit='1001')
        errors = _fe001_errors(yaml)
        assert any('limit' in e.lower() for e in errors)

    def test_query_limit_negative(self):
        """queryLimit -1 → out of range error."""
        yaml = _make_database_yaml(node_type='43', limit='-1')
        errors = _fe001_errors(yaml)
        assert any('limit' in e.lower() for e in errors)

    def test_whitespace_only_sql(self):
        """SQL that is only whitespace → error."""
        yaml = _make_database_yaml(sql='   ')
        errors = _fe001_errors(yaml)
        assert any('sql' in e.lower() for e in errors)


# ── Edge cases ──────────────────────────────────────────────────

class TestFE001_Database_EdgeCases:
    """Edge cases for database node validation."""

    def test_sql_with_special_chars(self):
        """SQL with special chars (no quotes) → valid."""
        yaml = _make_database_yaml(sql="SELECT * FROM users WHERE id > 0 AND status != 1")
        errors = _fe001_errors(yaml)
        assert not any('sql' in e.lower() for e in errors)

    def test_limit_as_ref_skipped(self):
        """queryLimit as ref (not literal) → range check skipped."""
        yaml = """
nodes:
  - id: '100001'
    type: '1'
    data:
      nodeMeta:
        title: Start
  - id: 'db1'
    type: '43'
    data:
      nodeMeta:
        title: Database
      inputs:
        inputParameters: []
        sql: 'SELECT 1'
        databaseInfoList:
          - id: db-1
        selectParam:
          limit:
            type: ref
            content:
              source: block-output
              blockId: '100001'
              name: limit
  - id: '900001'
    type: '2'
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: '100001'
    targetNodeID: 'db1'
  - sourceNodeID: 'db1'
    targetNodeID: '900001'
"""
        errors = _fe001_errors(yaml)
        assert not any('limit' in e.lower() for e in errors)
