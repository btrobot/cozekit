"""FE-012: Exception JSON parseability validation.

When a node has onError config with returnJson,
the JSON string must be parseable.

Covers:
  - No onError config → no error
  - Valid JSON in returnJson → no error
  - Invalid JSON in returnJson → error
  - Empty returnJson → no error
  - Non-string returnJson → no error
"""
from __future__ import annotations

from tests.conftest import compile_text


def _fe012_errors(yaml_text: str) -> list[str]:
    return [d.message for d in compile_text(yaml_text).diagnostics
            if d.rule_id == 'SEMANTIC-FE-012']


def _make_exception_json_yaml(return_json: str | None = None) -> str:
    """Build workflow with optional returnJson in onError."""
    if return_json is None:
        on_error_block = ''
    else:
        on_error_block = (
            f"\n      onError:\n"
            f"        settingOnErrorIsOpen: true\n"
            f"        processType: 'redirect'\n"
            f"        returnJson: '{return_json}'"
        )

    return f"""
nodes:
  - id: '100001'
    type: '1'
    data:
      nodeMeta:
        title: Start
  - id: 'n1'
    type: '3'
    data:
      nodeMeta:
        title: LLM
      llmParam:
        modelType: '1'
        prompt: 'test'{on_error_block}
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


class TestFE012_Positive:
    """No FE-012 errors expected."""

    def test_no_on_error(self):
        """No onError → no error."""
        assert not _fe012_errors(_make_exception_json_yaml())

    def test_valid_json(self):
        """Valid JSON → no error."""
        yaml = _make_exception_json_yaml(return_json='{"key": "value"}')
        assert not _fe012_errors(yaml)

    def test_empty_return_json(self):
        """Empty returnJson → no error."""
        yaml = _make_exception_json_yaml(return_json='')
        assert not _fe012_errors(yaml)

    def test_valid_json_array(self):
        """Valid JSON array → no error."""
        yaml = _make_exception_json_yaml(return_json='[1, 2, 3]')
        assert not _fe012_errors(yaml)


class TestFE012_Negative:
    """FE-012 errors expected."""

    def test_invalid_json(self):
        """Invalid JSON → error."""
        yaml = _make_exception_json_yaml(return_json='{bad json}')
        errors = _fe012_errors(yaml)
        assert len(errors) >= 1
        assert 'json' in errors[0].lower()

    def test_incomplete_json(self):
        """Incomplete JSON → error."""
        yaml = _make_exception_json_yaml(return_json='{"key": "value"')
        errors = _fe012_errors(yaml)
        assert len(errors) >= 1

    def test_plain_text(self):
        """Plain text (not JSON) → error."""
        yaml = _make_exception_json_yaml(return_json='not json at all')
        errors = _fe012_errors(yaml)
        assert len(errors) >= 1
