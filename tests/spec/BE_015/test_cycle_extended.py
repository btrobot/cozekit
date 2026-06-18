"""BE-015: Extended cycle detection tests.

Additional scenarios beyond the basic 2-node cycle in test_cycle_detection.py:
  - 3-node cycle (A→B→C→A)
  - Diamond graph without cycle (valid)
  - Self-loop edge (A→A)
  - Cycle with branch node
  - Per-canvas boundary regression (batch/loop back-edges)

规则来源: backend-rules.json BE-DetectCycles-001, coze-workflow-spec.md §3.6.4
"""
from __future__ import annotations

from tests.conftest import compile_text


def _be015_ids(t):
    return [d.rule_id for d in compile_text(t).diagnostics if d.rule_id == 'SEMANTIC-BE-015']


class TestBE015_Extended_Positive:
    """Valid graph topologies — no cycle error."""

    def test_diamond_no_cycle(self):
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "n1"\n    type: "5"\n    data:\n      nodeMeta:\n        title: "A"\n'
            '  - id: "n2"\n    type: "5"\n    data:\n      nodeMeta:\n        title: "B"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n'
            '  - sourceNodeID: "100001"\n    targetNodeID: "n1"\n'
            '  - sourceNodeID: "100001"\n    targetNodeID: "n2"\n'
            '  - sourceNodeID: "n1"\n    targetNodeID: "900001"\n'
            '  - sourceNodeID: "n2"\n    targetNodeID: "900001"\n'
        )
        assert 'SEMANTIC-BE-015' not in _be015_ids(t)

    def test_linear_chain_no_cycle(self):
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "n1"\n    type: "5"\n    data:\n      nodeMeta:\n        title: "A"\n'
            '  - id: "n2"\n    type: "5"\n    data:\n      nodeMeta:\n        title: "B"\n'
            '  - id: "n3"\n    type: "5"\n    data:\n      nodeMeta:\n        title: "C"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n'
            '  - sourceNodeID: "100001"\n    targetNodeID: "n1"\n'
            '  - sourceNodeID: "n1"\n    targetNodeID: "n2"\n'
            '  - sourceNodeID: "n2"\n    targetNodeID: "n3"\n'
            '  - sourceNodeID: "n3"\n    targetNodeID: "900001"\n'
        )
        assert 'SEMANTIC-BE-015' not in _be015_ids(t)


class TestBE015_Extended_Negative:
    """Invalid graph topologies — cycle error."""

    def test_three_node_cycle(self):
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "n1"\n    type: "5"\n    data:\n      nodeMeta:\n        title: "A"\n'
            '  - id: "n2"\n    type: "5"\n    data:\n      nodeMeta:\n        title: "B"\n'
            '  - id: "n3"\n    type: "5"\n    data:\n      nodeMeta:\n        title: "C"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n'
            '  - sourceNodeID: "100001"\n    targetNodeID: "n1"\n'
            '  - sourceNodeID: "n1"\n    targetNodeID: "n2"\n'
            '  - sourceNodeID: "n2"\n    targetNodeID: "n3"\n'
            '  - sourceNodeID: "n3"\n    targetNodeID: "n1"\n'
            '  - sourceNodeID: "n3"\n    targetNodeID: "900001"\n'
        )
        assert 'SEMANTIC-BE-015' in _be015_ids(t)

    def test_self_loop(self):
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "n1"\n    type: "5"\n    data:\n      nodeMeta:\n        title: "A"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n'
            '  - sourceNodeID: "100001"\n    targetNodeID: "n1"\n'
            '  - sourceNodeID: "n1"\n    targetNodeID: "n1"\n'
            '  - sourceNodeID: "n1"\n    targetNodeID: "900001"\n'
        )
        assert 'SEMANTIC-BE-015' in _be015_ids(t)

    def test_cycle_not_including_start(self):
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "n1"\n    type: "5"\n    data:\n      nodeMeta:\n        title: "A"\n'
            '  - id: "n2"\n    type: "3"\n    data:\n      nodeMeta:\n        title: "LLM"\n'
            '  - id: "n3"\n    type: "5"\n    data:\n      nodeMeta:\n        title: "C"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n'
            '  - sourceNodeID: "100001"\n    targetNodeID: "n1"\n'
            '  - sourceNodeID: "n1"\n    targetNodeID: "n2"\n'
            '  - sourceNodeID: "n2"\n    targetNodeID: "n3"\n'
            '  - sourceNodeID: "n3"\n    targetNodeID: "n2"\n'
            '  - sourceNodeID: "n3"\n    targetNodeID: "900001"\n'
        )
        assert 'SEMANTIC-BE-015' in _be015_ids(t)


class TestBE015_CanvasBoundary:
    """Regression: per-canvas cycle detection.

    Composite nodes (batch/loop) have their own sub-canvas. Inner edges
    that loop back to the composite node owner represent valid iteration.
    coze-studio's DetectCycles checks each canvas independently.
    """

    def test_batch_inner_back_edge_not_cycle(self):
        """Batch inner: Start→Batch(inner: A→B→[back to batch])→End."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "batch1"\n    type: "28"\n    data:\n      nodeMeta:\n        title: "Batch"\n'
            '    blocks:\n'
            '      - id: "inner1"\n        type: "5"\n        data:\n          nodeMeta:\n            title: "Inner A"\n'
            '      - id: "inner2"\n        type: "5"\n        data:\n          nodeMeta:\n            title: "Inner B"\n'
            '    edges:\n'
            '      - sourceNodeID: "batch1"\n        targetNodeID: "inner1"\n'
            '      - sourceNodeID: "inner1"\n        targetNodeID: "inner2"\n'
            '      - sourceNodeID: "inner2"\n        targetNodeID: "batch1"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n'
            '  - sourceNodeID: "100001"\n    targetNodeID: "batch1"\n'
            '  - sourceNodeID: "batch1"\n    targetNodeID: "900001"\n'
        )
        assert 'SEMANTIC-BE-015' not in _be015_ids(t)

    def test_loop_inner_back_edge_not_cycle(self):
        """Loop inner: Start→Loop(inner: A→B→[back to loop])→End."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "loop1"\n    type: "21"\n    data:\n      nodeMeta:\n        title: "Loop"\n'
            '    blocks:\n'
            '      - id: "l_inner1"\n        type: "5"\n        data:\n          nodeMeta:\n            title: "Step A"\n'
            '      - id: "l_inner2"\n        type: "5"\n        data:\n          nodeMeta:\n            title: "Step B"\n'
            '    edges:\n'
            '      - sourceNodeID: "loop1"\n        targetNodeID: "l_inner1"\n'
            '      - sourceNodeID: "l_inner1"\n        targetNodeID: "l_inner2"\n'
            '      - sourceNodeID: "l_inner2"\n        targetNodeID: "loop1"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n'
            '  - sourceNodeID: "100001"\n    targetNodeID: "loop1"\n'
            '  - sourceNodeID: "loop1"\n    targetNodeID: "900001"\n'
        )
        assert 'SEMANTIC-BE-015' not in _be015_ids(t)

    def test_flat_cycle_still_detected(self):
        """Real cycle in flat canvas still caught."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "n1"\n    type: "5"\n    data:\n      nodeMeta:\n        title: "A"\n'
            '  - id: "n2"\n    type: "5"\n    data:\n      nodeMeta:\n        title: "B"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n'
            '  - sourceNodeID: "100001"\n    targetNodeID: "n1"\n'
            '  - sourceNodeID: "n1"\n    targetNodeID: "n2"\n'
            '  - sourceNodeID: "n2"\n    targetNodeID: "n1"\n'
            '  - sourceNodeID: "n2"\n    targetNodeID: "900001"\n'
        )
        assert 'SEMANTIC-BE-015' in _be015_ids(t)
