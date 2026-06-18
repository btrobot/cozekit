"""VAL-JSON-SCHEMA-001: 输出变量 defaultValue JSON Schema 校验。

规则来源: jsonSchemaValidator (coze-studio)
当输出变量声明了 type 且有 defaultValue 时：
  1. defaultValue 必须是合法 JSON
  2. JSON 值类型必须与声明的 type 兼容

类型映射:
  string  → JSON string
  integer → JSON integer/number
  number  → JSON integer/number
  float   → JSON integer/number
  boolean → JSON boolean
  object  → JSON object
  list    → JSON array
  time    → JSON string
"""
from __future__ import annotations

from tests.conftest import compile_text


def _fe013_errors(yaml_text: str) -> list[str]:
    return [d.message for d in compile_text(yaml_text).diagnostics
            if d.rule_id == 'SEMANTIC-FE-013']


def _make_output_yaml(name: str, var_type: str, default_value: str | None = None) -> str:
    dv_line = ''
    if default_value is not None:
        dv_line = f"\n          defaultValue: '{default_value}'"

    return f"""nodes:
  - id: '100001'
    type: '1'
    data:
      nodeMeta:
        title: Start
  - id: 'n1'
    type: '5'
    data:
      nodeMeta:
        title: Code
      outputs:
        - name: '{name}'
          type: '{var_type}'{dv_line}
  - id: '900001'
    type: '2'
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: '100001'
    targetNodeID: 'n1'
  - sourceNodeID: 'n1'
    targetNodeID: '900001'
"""


# ── Positive: valid defaultValue matching type ─────────────────

class TestDefaultValueSchema_Positive:
    """Valid defaultValue → no errors."""

    def test_string_type_with_string_value(self):
        yaml = _make_output_yaml('result', 'string', '"hello"')
        errors = _fe013_errors(yaml)
        assert not any('defaultValue' in e for e in errors)

    def test_integer_type_with_int_value(self):
        yaml = _make_output_yaml('count', 'integer', '42')
        errors = _fe013_errors(yaml)
        assert not any('defaultValue' in e for e in errors)

    def test_number_type_with_float_value(self):
        yaml = _make_output_yaml('score', 'number', '3.14')
        errors = _fe013_errors(yaml)
        assert not any('defaultValue' in e for e in errors)

    def test_float_type_with_float_value(self):
        yaml = _make_output_yaml('ratio', 'float', '0.5')
        errors = _fe013_errors(yaml)
        assert not any('defaultValue' in e for e in errors)

    def test_boolean_type_with_bool_value(self):
        yaml = _make_output_yaml('flag', 'boolean', 'true')
        errors = _fe013_errors(yaml)
        assert not any('defaultValue' in e for e in errors)

    def test_object_type_with_object_value(self):
        yaml = _make_output_yaml('data', 'object', '{"key": "value"}')
        errors = _fe013_errors(yaml)
        assert not any('defaultValue' in e for e in errors)

    def test_list_type_with_array_value(self):
        yaml = _make_output_yaml('items', 'list', '[1, 2, 3]')
        errors = _fe013_errors(yaml)
        assert not any('defaultValue' in e for e in errors)

    def test_time_type_with_string_value(self):
        yaml = _make_output_yaml('timestamp', 'time', '"2024-01-01"')
        errors = _fe013_errors(yaml)
        assert not any('defaultValue' in e for e in errors)

    def test_no_default_value(self):
        """No defaultValue → no error."""
        yaml = _make_output_yaml('result', 'string')
        errors = _fe013_errors(yaml)
        assert not any('defaultValue' in e for e in errors)

    def test_integer_type_with_number_value(self):
        """integer type accepts JSON number (42.0)."""
        yaml = _make_output_yaml('count', 'integer', '42.0')
        errors = _fe013_errors(yaml)
        assert not any('defaultValue' in e for e in errors)


# ── Negative: invalid defaultValue ─────────────────────────────

class TestDefaultValueSchema_Negative:
    """Invalid defaultValue → errors."""

    def test_invalid_json(self):
        """Not valid JSON → error."""
        yaml = _make_output_yaml('data', 'object', '{bad json}')
        errors = _fe013_errors(yaml)
        assert any('not valid JSON' in e for e in errors)

    def test_string_type_with_int_value(self):
        """string type with JSON int → type mismatch."""
        yaml = _make_output_yaml('result', 'string', '42')
        errors = _fe013_errors(yaml)
        assert any('does not match' in e for e in errors)

    def test_integer_type_with_string_value(self):
        """integer type with JSON string → type mismatch."""
        yaml = _make_output_yaml('count', 'integer', '"hello"')
        errors = _fe013_errors(yaml)
        assert any('does not match' in e for e in errors)

    def test_boolean_type_with_string_value(self):
        """boolean type with JSON string → type mismatch."""
        yaml = _make_output_yaml('flag', 'boolean', '"yes"')
        errors = _fe013_errors(yaml)
        assert any('does not match' in e for e in errors)

    def test_object_type_with_array_value(self):
        """object type with JSON array → type mismatch."""
        yaml = _make_output_yaml('data', 'object', '[1, 2]')
        errors = _fe013_errors(yaml)
        assert any('does not match' in e for e in errors)

    def test_list_type_with_object_value(self):
        """list type with JSON object → type mismatch."""
        yaml = _make_output_yaml('items', 'list', '{"key": "value"}')
        errors = _fe013_errors(yaml)
        assert any('does not match' in e for e in errors)

    def test_plain_text_not_json(self):
        """Plain text (not JSON) → error."""
        yaml = _make_output_yaml('result', 'string', 'just plain text')
        errors = _fe013_errors(yaml)
        assert any('not valid JSON' in e for e in errors)


# ── Edge cases ─────────────────────────────────────────────────

class TestDefaultValueSchema_EdgeCases:
    """Edge cases for defaultValue validation."""

    def test_empty_default_value(self):
        """Empty string defaultValue → no error (skipped)."""
        yaml = _make_output_yaml('result', 'string', '')
        errors = _fe013_errors(yaml)
        assert not any('defaultValue' in e for e in errors)

    def test_nested_object_valid(self):
        """Nested object with correct types → no error."""
        yaml = _make_output_yaml('config', 'object', '{"name": "test", "count": 5}')
        errors = _fe013_errors(yaml)
        assert not any('defaultValue' in e for e in errors)

    def test_mixed_array_valid(self):
        """Array with mixed types → no error for list type."""
        yaml = _make_output_yaml('items', 'list', '["a", "b", "c"]')
        errors = _fe013_errors(yaml)
        assert not any('defaultValue' in e for e in errors)

    def test_null_json_value(self):
        """JSON null → type mismatch for any declared type."""
        yaml = _make_output_yaml('result', 'string', 'null')
        errors = _fe013_errors(yaml)
        assert any('does not match' in e for e in errors)
