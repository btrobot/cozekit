"""FE-014: Generic input parameter validation.

Validates that input parameters (inputParameters):
  - Have non-empty names
  - Names match identifier format (same regex as output names)
  - Have non-empty values
  - Sibling names are unique

Matches coze-studio inputTreeValidator + valueExpressionValidator.
"""
from __future__ import annotations

from tests.conftest import compile_text


def _fe014_ids(t):
    return [d.rule_id for d in compile_text(t).diagnostics if d.rule_id == 'SEMANTIC-FE-014']


def _fe014_messages(t):
    return [d.message for d in compile_text(t).diagnostics if d.rule_id == 'SEMANTIC-FE-014']


def _make_workflow_with_inputs(inputs_yaml: str) -> str:
    return f"""nodes:
  - id: '100001'
    type: '1'
    data:
      nodeMeta:
        title: Start
  - id: 'llm1'
    type: '3'
    data:
      nodeMeta:
        title: LLM
      inputs:
        inputParameters:
{inputs_yaml}
        llmParam:
          - name: modelType
            input:
              type: integer
              value:
                type: literal
                content: '1001'
  - id: '900001'
    type: '2'
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: '100001'
    targetNodeID: 'llm1'
  - sourceNodeID: 'llm1'
    targetNodeID: '900001'
"""


# ── Positive ─────────────────────────────────────────────────────

class TestFE014_Positive:
    def test_valid_input(self):
        t = _make_workflow_with_inputs(
            "          - name: prompt\n"
            "            input:\n"
            "              type: string\n"
            "              value:\n"
            "                type: literal\n"
            "                content: 'hello'"
        )
        assert 'SEMANTIC-FE-014' not in _fe014_ids(t)

    def test_valid_ref_input(self):
        t = _make_workflow_with_inputs(
            "          - name: prompt\n"
            "            input:\n"
            "              type: string\n"
            "              value:\n"
            "                type: ref\n"
            "                content:\n"
            "                  source: block-output\n"
            "                  blockID: '100001'\n"
            "                  name: output"
        )
        assert 'SEMANTIC-FE-014' not in _fe014_ids(t)

    def test_valid_global_ref_input(self):
        t = _make_workflow_with_inputs(
            "          - name: prompt\n"
            "            input:\n"
            "              type: string\n"
            "              value:\n"
            "                type: ref\n"
            "                content:\n"
            "                  source: global_variable_app\n"
            "                  path:\n"
            "                    - app_v1\n"
            "                  blockID: '100001'"
        )
        assert 'SEMANTIC-FE-014' not in _fe014_ids(t)

    def test_multiple_valid_inputs(self):
        t = _make_workflow_with_inputs(
            "          - name: input1\n"
            "            input:\n"
            "              type: string\n"
            "              value:\n"
            "                type: literal\n"
            "                content: 'a'\n"
            "          - name: input2\n"
            "            input:\n"
            "              type: string\n"
            "              value:\n"
            "                type: literal\n"
            "                content: 'b'"
        )
        assert 'SEMANTIC-FE-014' not in _fe014_ids(t)

    def test_underscore_name(self):
        t = _make_workflow_with_inputs(
            "          - name: _private\n"
            "            input:\n"
            "              type: string\n"
            "              value:\n"
            "                type: literal\n"
            "                content: 'x'"
        )
        assert 'SEMANTIC-FE-014' not in _fe014_ids(t)

    def test_no_inputs_no_error(self):
        """Node with no inputParameters should not trigger FE-014."""
        t = """nodes:
  - id: '100001'
    type: '1'
    data:
      nodeMeta:
        title: Start
  - id: '900001'
    type: '2'
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: '100001'
    targetNodeID: '900001'
"""
        assert 'SEMANTIC-FE-014' not in _fe014_ids(t)


# ── Negative: Name Format ────────────────────────────────────────

class TestFE014_NameFormat:
    def test_empty_name(self):
        t = _make_workflow_with_inputs(
            "          - name: ''\n"
            "            input:\n"
            "              type: string\n"
            "              value:\n"
            "                type: literal\n"
            "                content: 'x'"
        )
        assert 'SEMANTIC-FE-014' in _fe014_ids(t)

    def test_starts_with_digit(self):
        t = _make_workflow_with_inputs(
            "          - name: 123bad\n"
            "            input:\n"
            "              type: string\n"
            "              value:\n"
            "                type: literal\n"
            "                content: 'x'"
        )
        assert 'SEMANTIC-FE-014' in _fe014_ids(t)

    def test_contains_hyphen(self):
        t = _make_workflow_with_inputs(
            "          - name: my-var\n"
            "            input:\n"
            "              type: string\n"
            "              value:\n"
            "                type: literal\n"
            "                content: 'x'"
        )
        assert 'SEMANTIC-FE-014' in _fe014_ids(t)

    def test_contains_dot(self):
        t = _make_workflow_with_inputs(
            "          - name: my.var\n"
            "            input:\n"
            "              type: string\n"
            "              value:\n"
            "                type: literal\n"
            "                content: 'x'"
        )
        assert 'SEMANTIC-FE-014' in _fe014_ids(t)

    def test_contains_space(self):
        t = _make_workflow_with_inputs(
            "          - name: my var\n"
            "            input:\n"
            "              type: string\n"
            "              value:\n"
            "                type: literal\n"
            "                content: 'x'"
        )
        assert 'SEMANTIC-FE-014' in _fe014_ids(t)

    def test_reserved_word_true(self):
        t = _make_workflow_with_inputs(
            "          - name: true\n"
            "            input:\n"
            "              type: boolean\n"
            "              value:\n"
            "                type: literal\n"
            "                content: 'true'"
        )
        assert 'SEMANTIC-FE-014' in _fe014_ids(t)

    def test_reserved_word_null(self):
        t = _make_workflow_with_inputs(
            "          - name: null\n"
            "            input:\n"
            "              type: string\n"
            "              value:\n"
            "                type: literal\n"
            "                content: 'null'"
        )
        assert 'SEMANTIC-FE-014' in _fe014_ids(t)


# ── Negative: Value Required ─────────────────────────────────────

class TestFE014_ValueRequired:
    def test_missing_input_field(self):
        """Parameter with no input field → value required error."""
        t = _make_workflow_with_inputs("          - name: prompt")
        ids = _fe014_ids(t)
        assert len(ids) >= 1

    def test_empty_literal_value(self):
        """Parameter with empty literal value → value required error."""
        t = _make_workflow_with_inputs(
            "          - name: prompt\n"
            "            input:\n"
            "              type: string\n"
            "              value:\n"
            "                type: literal\n"
            "                content: ''"
        )
        ids = _fe014_ids(t)
        assert len(ids) >= 1


# ── Negative: Sibling Uniqueness ─────────────────────────────────

class TestFE014_Uniqueness:
    def test_duplicate_sibling_names(self):
        t = _make_workflow_with_inputs(
            "          - name: prompt\n"
            "            input:\n"
            "              type: string\n"
            "              value:\n"
            "                type: literal\n"
            "                content: 'a'\n"
            "          - name: prompt\n"
            "            input:\n"
            "              type: string\n"
            "              value:\n"
            "                type: literal\n"
            "                content: 'b'"
        )
        ids = _fe014_ids(t)
        assert len(ids) >= 1

    def test_unique_names_no_error(self):
        t = _make_workflow_with_inputs(
            "          - name: input1\n"
            "            input:\n"
            "              type: string\n"
            "              value:\n"
            "                type: literal\n"
            "                content: 'a'\n"
            "          - name: input2\n"
            "            input:\n"
            "              type: string\n"
            "              value:\n"
            "                type: literal\n"
            "                content: 'b'"
        )
        assert 'SEMANTIC-FE-014' not in _fe014_ids(t)


# ── Negative: Multiple Errors ────────────────────────────────────

class TestFE014_MultipleErrors:
    def test_name_and_value_both_invalid(self):
        """Invalid name + missing value → at least 2 errors."""
        t = _make_workflow_with_inputs(
            "          - name: bad-name\n"
            "            input:\n"
            "              type: string\n"
        )
        ids = _fe014_ids(t)
        assert len(ids) >= 2
