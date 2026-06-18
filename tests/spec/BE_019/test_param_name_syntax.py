"""BE-019: parameter name syntax validation."""
from __future__ import annotations
from tests.conftest import compile_text

def _be_ids(t):
    return [d.rule_id for d in compile_text(t).diagnostics if d.rule_id.startswith('SEMANTIC-BE')]

def _yaml_with_param(name):
    return (
        'nodes:\n'
        f'  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
        f'  - id: "n1"\n    type: "5"\n    data:\n      nodeMeta:\n        title: "Code"\n'
        f'      inputs:\n        inputParameters:\n          - name: "{name}"\n            input:\n              type: string\n              value:\n                type: literal\n                content: hi\n'
        f'  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
        'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "n1"\n  - sourceNodeID: "n1"\n    targetNodeID: "900001"\n'
    )

class TestBE019_Positive:
    def test_valid_name(self):
        assert 'SEMANTIC-BE-019' not in _be_ids(_yaml_with_param('myVar'))
    def test_underscore_start(self):
        assert 'SEMANTIC-BE-019' not in _be_ids(_yaml_with_param('_private'))

class TestBE019_Negative:
    def test_invalid_name(self):
        assert 'SEMANTIC-BE-019' in _be_ids(_yaml_with_param('123bad'))
