"""BE-002: non-start nodes must have incoming edge."""
from __future__ import annotations
from tests.conftest import compile_text

def _be_ids(t):
    return [d.rule_id for d in compile_text(t).diagnostics if d.rule_id.startswith('SEMANTIC-BE')]

class TestBE002_Positive:
    def test_connected_node(self):
        assert 'SEMANTIC-BE-002' not in _be_ids(
            'nodes:\n  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "n1"\n    type: "5"\n    data:\n      nodeMeta:\n        title: "Code"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "n1"\n  - sourceNodeID: "n1"\n    targetNodeID: "900001"\n'
        )

class TestBE002_Negative:
    def test_node_no_incoming(self):
        ids = _be_ids(
            'nodes:\n  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "n1"\n    type: "5"\n    data:\n      nodeMeta:\n        title: "Code"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "900001"\n'
        )
        assert 'SEMANTIC-BE-002' in ids


class TestBE002_BreakContinue:
    """Break/Continue are loop-control terminal nodes — no outgoing edges needed."""

    def test_break_no_outgoing_not_flagged(self):
        """Break node inside a loop — no outgoing edges is OK."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "loop1"\n    type: "21"\n    data:\n      nodeMeta:\n        title: "Loop"\n'
            '    blocks:\n'
            '      - id: "cond1"\n        type: "8"\n        data:\n          nodeMeta:\n            title: "Condition"\n'
            '      - id: "brk"\n        type: "19"\n        data:\n          nodeMeta:\n            title: "Break"\n'
            '    edges:\n'
            '      - sourceNodeID: "loop1"\n        targetNodeID: "cond1"\n'
            '      - sourceNodeID: "cond1"\n        targetNodeID: "brk"\n'
            '        sourcePortID: "true"\n'
            '      - sourceNodeID: "cond1"\n        targetNodeID: "loop1"\n'
            '        sourcePortID: "false"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n'
            '  - sourceNodeID: "100001"\n    targetNodeID: "loop1"\n'
            '  - sourceNodeID: "loop1"\n    targetNodeID: "900001"\n'
        )
        be002 = [d for d in compile_text(t).diagnostics if d.rule_id == 'SEMANTIC-BE-002']
        assert not any('brk' in d.message for d in be002)

    def test_continue_no_outgoing_not_flagged(self):
        """Continue node inside a loop — no outgoing edges is OK."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "loop1"\n    type: "21"\n    data:\n      nodeMeta:\n        title: "Loop"\n'
            '    blocks:\n'
            '      - id: "code1"\n        type: "5"\n        data:\n          nodeMeta:\n            title: "Code"\n'
            '      - id: "cont"\n        type: "29"\n        data:\n          nodeMeta:\n            title: "Continue"\n'
            '    edges:\n'
            '      - sourceNodeID: "loop1"\n        targetNodeID: "code1"\n'
            '      - sourceNodeID: "code1"\n        targetNodeID: "cont"\n'
            '      - sourceNodeID: "cont"\n        targetNodeID: "loop1"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n'
            '  - sourceNodeID: "100001"\n    targetNodeID: "loop1"\n'
            '  - sourceNodeID: "loop1"\n    targetNodeID: "900001"\n'
        )
        be002 = [d for d in compile_text(t).diagnostics if d.rule_id == 'SEMANTIC-BE-002']
        assert not any('cont' in d.message for d in be002)
