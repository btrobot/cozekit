"""SYNTAX-018: object/list variables must have schema."""
from __future__ import annotations
from tests.conftest import compile_text

VALID = (
    'nodes:\n'
    '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
    '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
    'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "900001"\n'
)

def _ids(t):
    return [d.rule_id for d in compile_text(t).diagnostics if d.rule_id.startswith('SYNTAX')]

def _add_var(vtype, schema=None):
    schema_line = f'        schema:\n          type: "{schema}"' if schema else ''
    return VALID.replace(
        '  - id: "900001"',
        f'  - id: "var1"\n    type: "11"\n    data:\n      nodeMeta:\n        title: "Var"\n      inputs:\n        name: "myVar"\n        type: "{vtype}"\n{schema_line}\n  - id: "900001"'
    )

class TestSYNTAX018_Positive:
    def test_object_with_schema(self):
        assert 'SYNTAX-018' not in _ids(_add_var('object', 'object'))
    def test_list_with_schema(self):
        assert 'SYNTAX-018' not in _ids(_add_var('list', 'string'))
    def test_scalar_no_schema(self):
        assert 'SYNTAX-018' not in _ids(_add_var('string'))

class TestSYNTAX018_Negative:
    def test_object_without_schema(self):
        assert 'SYNTAX-018' in _ids(_add_var('object'))
    def test_list_without_schema(self):
        assert 'SYNTAX-018' in _ids(_add_var('list'))
