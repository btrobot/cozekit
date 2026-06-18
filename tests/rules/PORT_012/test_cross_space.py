"""PORTABILITY-012: cross-space blocked node types."""
from __future__ import annotations
import pytest
from tests.conftest import compile_text

def _port_ids(t):
    return [d.rule_id for d in compile_text(t).diagnostics if d.rule_id.startswith('PORTABILITY')]

def _make_yaml(type_id, label):
    return (
        'nodes:\n'
        '  - id: "100001"\n'
        '    type: "1"\n'
        '    data:\n'
        '      nodeMeta:\n'
        '        title: "Start"\n'
        '  - id: "n1"\n'
        f'    type: "{type_id}"\n'
        '    data:\n'
        '      nodeMeta:\n'
        f'        title: "{label}"\n'
        '  - id: "900001"\n'
        '    type: "2"\n'
        '    data:\n'
        '      nodeMeta:\n'
        '        title: "End"\n'
        'edges:\n'
        '  - sourceNodeID: "100001"\n'
        '    targetNodeID: "n1"\n'
        '  - sourceNodeID: "n1"\n'
        '    targetNodeID: "900001"\n'
    )

class TestPORT012_Negative:
    @pytest.mark.parametrize("type_id,label", [
        ('9', 'SubWorkflow'),
        ('6', 'Dataset'),
        ('27', 'DatasetWrite'),
        ('14', 'ImageFlow'),
        ('42', 'DatabaseCRUD'),
    ])
    def test_blocked_types_fire(self, type_id, label):
        assert 'PORTABILITY-012' in _port_ids(_make_yaml(type_id, label))
