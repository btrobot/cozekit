"""BE-017: empty blockID in reference."""
from __future__ import annotations
from tests.conftest import compile_text

def _be_ids(t):
    return [d.rule_id for d in compile_text(t).diagnostics if d.rule_id.startswith('SEMANTIC-BE')]

class TestBE017_Negative:
    def test_empty_blockid_fires(self):
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "n1"\n    type: "5"\n    data:\n      nodeMeta:\n        title: "Code"\n'
            '      inputs:\n        inputParameters:\n          - name: "x"\n            input:\n              type: string\n              value:\n                type: ref\n                content:\n                  source: block-output\n                  blockId: ""\n                  name: out\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "n1"\n  - sourceNodeID: "n1"\n    targetNodeID: "900001"\n'
        )
        assert 'SEMANTIC-BE-017' in _be_ids(t)
