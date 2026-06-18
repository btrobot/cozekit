"""SYNTAX-016/017/020: global variable structure validation."""
from __future__ import annotations
from tests.conftest import compile_text

def _all_ids(t):
    return [d.rule_id for d in compile_text(t).diagnostics]

def _var_yaml(name=None, vtype=None):
    parts = []
    if name: parts.append(f'        name: "{name}"')
    if vtype: parts.append(f'        type: "{vtype}"')
    inputs = '\n'.join(parts) if parts else ''
    return (
        'nodes:\n'
        '  - id: "100001"\n    type: "1"\n    data: {}\n'
        f'  - id: "11"\n    type: "11"\n    data:\n      inputs:\n{inputs}\n'
        '  - id: "900001"\n    type: "2"\n    data: {}\n'
        'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "11"\n  - sourceNodeID: "11"\n    targetNodeID: "900001"\n'
    )

class TestSYNTAX016_017_020_Positive:
    def test_variable_with_name_and_type(self):
        ids = _all_ids(_var_yaml('myVar', 'string'))
        assert 'SYNTAX-016' not in ids
        assert 'SYNTAX-017' not in ids
        assert 'SYNTAX-020' not in ids

class TestSYNTAX016_017_020_Negative:
    def test_missing_name(self):
        assert 'SYNTAX-016' in _all_ids(_var_yaml(None, 'string'))
    def test_missing_type(self):
        assert 'SYNTAX-017' in _all_ids(_var_yaml('myVar', None))
    def test_invalid_type(self):
        assert 'SYNTAX-020' in _all_ids(_var_yaml('myVar', 'invalid_type'))
