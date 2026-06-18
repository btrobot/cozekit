"""FE-001: Batch node (type 28) field validation.

Validates:
  - nodeMeta title validation
  - inputParameters name format + uniqueness
  - inputParameters value required
  - outputs name format + uniqueness
"""
from __future__ import annotations

from tests.conftest import compile_text


def _fe_errors(yaml_text: str) -> list[str]:
    """Extract SEMANTIC-FE-001 and SEMANTIC-FE-014 diagnostics."""
    report = compile_text(yaml_text)
    return [d.message for d in report.diagnostics
            if d.rule_id in ('SEMANTIC-FE-001', 'SEMANTIC-FE-013', 'SEMANTIC-FE-014')]


def _make_batch_yaml(
    title: str = 'Batch',
    input_params: str = '          []',
    outputs: str = '',
) -> str:
    """Build a minimal workflow with a batch node (type 28)."""
    outputs_section = f'\n      outputs:\n{outputs}' if outputs else ''
    return f"""
nodes:
  - id: '100001'
    type: '1'
    data:
      nodeMeta:
        title: Start
  - id: 'b1'
    type: '28'
    data:
      nodeMeta:
        title: '{title}'
      inputs:
        inputParameters:
{input_params}{outputs_section}
  - id: '900001'
    type: '2'
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: '100001'
    targetNodeID: 'b1'
  - sourceNodeID: 'b1'
    targetNodeID: '900001'
"""


def _input(name: str, value: str = 'value') -> str:
    return (
        f"          - name: '{name}'\n"
        f"            input:\n"
        f"              type: string\n"
        f"              value:\n"
        f"                type: literal\n"
        f"                content: '{value}'"
    )


# -- Positive --

class TestBatchPositive:
    def test_empty_inputs(self):
        yaml = _make_batch_yaml()
        assert not _fe_errors(yaml)

    def test_valid_input(self):
        yaml = _make_batch_yaml(input_params=_input('item', 'v1'))
        assert not _fe_errors(yaml)

    def test_valid_multiple_inputs(self):
        params = _input('item1', 'a') + '\n' + _input('item2', 'b')
        yaml = _make_batch_yaml(input_params=params)
        assert not _fe_errors(yaml)

    def test_valid_outputs(self):
        yaml = _make_batch_yaml(outputs="        - name: 'result'\n          type: string")
        assert not _fe_errors(yaml)


# -- Negative: input name --

class TestBatchInputName:
    def test_empty_input_name(self):
        yaml = _make_batch_yaml(input_params=_input('', 'v'))
        errors = _fe_errors(yaml)
        assert any('name' in e.lower() for e in errors)

    def test_invalid_input_name_format(self):
        yaml = _make_batch_yaml(input_params=_input('bad-name', 'v'))
        errors = _fe_errors(yaml)
        assert any('format' in e.lower() for e in errors)

    def test_duplicate_input_names(self):
        params = _input('item', 'a') + '\n' + _input('item', 'b')
        yaml = _make_batch_yaml(input_params=params)
        errors = _fe_errors(yaml)
        assert any('duplicate' in e.lower() for e in errors)


# -- Negative: input value --

class TestBatchInputValue:
    def test_missing_input_value(self):
        yaml = _make_batch_yaml(input_params="          - name: 'param1'")
        errors = _fe_errors(yaml)
        assert any('value' in e.lower() for e in errors)


# -- Negative: output name --

class TestBatchOutputName:
    def test_empty_output_name(self):
        yaml = _make_batch_yaml(outputs="        - name: ''\n          type: string")
        errors = _fe_errors(yaml)
        assert any('name' in e.lower() for e in errors)

    def test_invalid_output_name_format(self):
        yaml = _make_batch_yaml(outputs="        - name: 'bad-name'\n          type: string")
        errors = _fe_errors(yaml)
        assert any('format' in e.lower() for e in errors)
