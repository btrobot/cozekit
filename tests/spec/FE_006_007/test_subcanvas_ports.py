"""FE-006/007: subcanvas entry/exit port validation."""
from __future__ import annotations
from tests.conftest import compile_text

def _fe_ids(t):
    return sorted(d.rule_id for d in compile_text(t).diagnostics if d.rule_id.startswith('SEMANTIC-FE'))

_LOOP_OK = (
    'nodes:\n'
    '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
    '  - id: "loop-1"\n    type: "21"\n    data:\n      nodeMeta:\n        title: "Loop"\n'
    '    blocks:\n      - id: "inner"\n        type: "5"\n        data:\n          nodeMeta:\n            title: "Code"\n'
    '    edges:\n'
    '      - sourceNodeID: "loop-1"\n        targetPortID: "loop-function-inline-input"\n        targetNodeID: "inner"\n'
    '      - sourceNodeID: "inner"\n        sourcePortID: "loop-function-inline-output"\n        targetNodeID: "loop-1"\n'
    '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
    'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "loop-1"\n  - sourceNodeID: "loop-1"\n    targetNodeID: "900001"\n'
)

class TestFE006_007_Positive:
    def test_loop_with_ports_ok(self):
        ids = _fe_ids(_LOOP_OK)
        assert 'SEMANTIC-FE-006' not in ids
        assert 'SEMANTIC-FE-007' not in ids

class TestFE006_007_Negative:
    def test_loop_missing_entry_port(self):
        t = _LOOP_OK.replace(
            '      - sourceNodeID: "loop-1"\n        targetPortID: "loop-function-inline-input"\n        targetNodeID: "inner"\n', ''
        )
        ids = _fe_ids(t)
        assert 'SEMANTIC-FE-006' in ids or 'SEMANTIC-FE-007' in ids
