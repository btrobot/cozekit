"""FE-008: Exception port connectivity validation.

When a node has onError config with exception branch set,
the exception port must have an outgoing edge.

Covers:
  - No onError config → no error
  - onError set but no exception port edge → error
  - onError set with exception port edge → no error
  - onError with processType=abort → no error (no exception branch)
"""
from __future__ import annotations

from tests.conftest import compile_text


def _fe008_errors(yaml_text: str) -> list[str]:
    return [d.message for d in compile_text(yaml_text).diagnostics
            if d.rule_id == 'SEMANTIC-FE-008']


def _make_exception_yaml(
    on_error: str | None = None,
    exception_edge: bool = False,
) -> str:
    """Build workflow with optional onError config on the middle node."""
    on_error_block = ''
    if on_error:
        on_error_block = f'\n      onError:\n{on_error}'

    exception_edge_line = ''
    if exception_edge:
        exception_edge_line = (
            "\n  - sourceNodeID: 'n1'\n    targetNodeID: 'handler'\n"
            "    sourcePortID: 'exception'\n"
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
  - id: 'handler'
    type: '2'
    data:
      nodeMeta:
        title: ErrorHandler
edges:
  - sourceNodeID: '100001'
    targetNodeID: 'n1'
  - sourceNodeID: 'n1'
    targetNodeID: '900001'
{exception_edge_line}"""


class TestFE008_Positive:
    """No FE-008 errors expected."""

    def test_no_on_error_config(self):
        """No onError → no error."""
        yaml = _make_exception_yaml()
        assert not _fe008_errors(yaml)

    def test_exception_port_connected(self):
        """onError set with exception port edge → no error."""
        yaml = _make_exception_yaml(
            on_error="        settingOnErrorIsOpen: true\n        processType: 'redirect'",
            exception_edge=True,
        )
        assert not _fe008_errors(yaml)


class TestFE008_Negative:
    """FE-008 errors expected."""

    def test_exception_branch_no_edge(self):
        """onError set with redirect but no exception port edge → error."""
        yaml = _make_exception_yaml(
            on_error="        settingOnErrorIsOpen: true\n        processType: 'redirect'",
            exception_edge=False,
        )
        errors = _fe008_errors(yaml)
        assert len(errors) >= 1
        assert 'exception' in errors[0].lower()


class TestFE008_EdgeCases:
    """Edge cases for exception port validation."""

    def test_abort_process_type(self):
        """onError with abort processType → no exception branch needed."""
        yaml = _make_exception_yaml(
            on_error="        settingOnErrorIsOpen: true\n        processType: 'abort'",
        )
        # abort doesn't set exception branch, so no error
        errors = _fe008_errors(yaml)
        assert not errors
